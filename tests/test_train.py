import os
import subprocess
import sys
from pathlib import Path

from train.train import train_model

ROOT = Path(__file__).resolve().parents[1]
VOWELS = "aeiou"


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
