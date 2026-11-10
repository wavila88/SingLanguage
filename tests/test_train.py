import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

import dbConf.database  # noqa: F401  carga .env antes de que los tests borren variables
import train.train as train_script
from train.train import train_model

ROOT = Path(__file__).resolve().parents[1]
VOWELS = "aeiou"
OLD_MODEL = b"old model bytes"


class FakeSampleRepository:
    def __init__(self, samples):
        self._samples = samples
        self.loaded = False

    def load_samples(self):
        self.loaded = True
        return list(self._samples)


def _samples():
    samples = []
    for index, label in enumerate(VOWELS):
        for shot in range(3):
            base = index * 10 + shot * 0.01
            samples.append((label, [base + i for i in range(63)]))
    return samples


def test_stored_samples_are_sent_to_training_and_model_is_written(tmp_path):
    repo = FakeSampleRepository(_samples())
    model_path = tmp_path / "vowel_model.pkl"

    result = train_model(repo, model_path)

    assert repo.loaded is True
    assert model_path.exists()
    assert isinstance(result.recognized_a, bool)


def test_second_run_replaces_the_same_model_file(tmp_path):
    repo = FakeSampleRepository(_samples())
    model_path = tmp_path / "vowel_model.pkl"

    train_model(repo, model_path)
    train_model(repo, model_path)

    assert sorted(p.name for p in tmp_path.iterdir()) == ["vowel_model.pkl"]


def test_held_out_a_sample_is_reported_as_recognized(tmp_path):
    repo = FakeSampleRepository(_samples())

    result = train_model(repo, tmp_path / "vowel_model.pkl")

    assert result.recognized_a is True


class EmptyCursor:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=None):
        pass

    def fetchall(self):
        return []


class EmptyConnection:
    def cursor(self):
        return EmptyCursor()

    def close(self):
        pass


def _run_main_expecting_error(monkeypatch, capsys, model_path):
    model_path.write_bytes(OLD_MODEL)
    monkeypatch.setattr(train_script, "MODEL_PATH", model_path)

    with pytest.raises(SystemExit) as exc:
        train_script.main()

    assert exc.value.code == 1
    assert "error" in capsys.readouterr().err.lower()
    assert model_path.read_bytes() == OLD_MODEL


def test_missing_database_url_prints_error_exits_1_and_keeps_model(monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    _run_main_expecting_error(monkeypatch, capsys, tmp_path / "vowel_model.pkl")


def test_unreachable_database_prints_error_exits_1_and_keeps_model(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://unreachable")

    def unreachable(url):
        raise psycopg.OperationalError("no se pudo conectar")

    monkeypatch.setattr("dbConf.database.connect", unreachable)

    _run_main_expecting_error(monkeypatch, capsys, tmp_path / "vowel_model.pkl")


def test_no_samples_prints_error_exits_1_and_keeps_model(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")
    monkeypatch.setattr("dbConf.database.connect", lambda url: EmptyConnection())

    _run_main_expecting_error(monkeypatch, capsys, tmp_path / "vowel_model.pkl")


def test_training_does_not_load_camera_or_database_driver():
    code = (
        "import sys; import train.train; "
        "print([m for m in ('camera', 'cv2', 'psycopg') if m in sys.modules])"
    )
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "[]"
