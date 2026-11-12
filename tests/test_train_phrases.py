import psycopg
import pytest

import dbConf.database  # noqa: F401  carga .env antes de que los tests borren variables
import train.train_phrases as phrases_script
from train.train_phrases import train_motion_model

OLD_MODEL = b"old motion model bytes"
NOT_ENOUGH = "Movimiento: se necesitan al menos 2 frases con 3 muestras; hay 1 (hola: 6)"


def _frames(count=6):
    hand = {"side": "right", "points": [0.0] * 63, "wrist": [0.5, 0.5, 0.0]}
    return [{"index": i, "ms": i * 100, "hands": [hand]} for i in range(count)]


class FakeMotionRepository:
    def __init__(self, samples):
        self._samples = samples

    def load_motion_samples(self):
        return list(self._samples)


class FakeConnection:
    def close(self):
        pass


def _only_hola():
    return [("hola", _frames()) for _ in range(6)]


def test_fewer_than_two_phrases_with_three_samples_writes_no_model(tmp_path):
    model_path = tmp_path / "motion_model.pkl"

    with pytest.raises(ValueError) as error:
        train_motion_model(FakeMotionRepository(_only_hola()), model_path)

    assert str(error.value) == NOT_ENOUGH
    assert not model_path.exists()


def test_a_phrase_with_fewer_than_three_samples_does_not_count(tmp_path):
    samples = _only_hola() + [("adios", _frames()), ("adios", _frames())]

    with pytest.raises(ValueError) as error:
        train_motion_model(FakeMotionRepository(samples), tmp_path / "motion_model.pkl")

    assert str(error.value) == "Movimiento: se necesitan al menos 2 frases con 3 muestras; hay 1 (hola: 6, adios: 2)"


def _run_main_expecting_error(monkeypatch, capsys, model_path):
    model_path.write_bytes(OLD_MODEL)
    monkeypatch.setattr(phrases_script, "MOTION_MODEL_PATH", model_path)

    with pytest.raises(SystemExit) as exc:
        phrases_script.main()

    assert exc.value.code == 1
    assert model_path.read_bytes() == OLD_MODEL
    return capsys.readouterr().err


def test_not_enough_phrases_from_main_says_why_and_exits_1(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")
    monkeypatch.setattr("dbConf.database.connect", lambda url: FakeConnection())
    monkeypatch.setattr("dbConf.database.PostgresSampleRepository", lambda conn: FakeMotionRepository(_only_hola()))

    err = _run_main_expecting_error(monkeypatch, capsys, tmp_path / "motion_model.pkl")

    assert NOT_ENOUGH in err


def test_missing_database_url_prints_error_exits_1_and_keeps_model(monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    err = _run_main_expecting_error(monkeypatch, capsys, tmp_path / "motion_model.pkl")

    assert "error" in err.lower()


def test_unreachable_database_prints_error_exits_1_and_keeps_model(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://unreachable")

    def unreachable(url):
        raise psycopg.OperationalError("no se pudo conectar")

    monkeypatch.setattr("dbConf.database.connect", unreachable)

    err = _run_main_expecting_error(monkeypatch, capsys, tmp_path / "motion_model.pkl")

    assert "error" in err.lower()
