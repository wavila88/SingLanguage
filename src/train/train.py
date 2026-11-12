"""DEPRECATED (spec 007): trains the one-hand static (vowel) model from `samples.points`, a column that no longer exists.
Kept in the repo until it is decided whether static signs return or everything goes through train_phrases.py."""
import os
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

MODEL_PATH = Path(__file__).resolve().parents[2] / "data" / "language_sing_model.pkl"
TARGET = "a"


@dataclass
class TrainingResult:
    recognized_a: bool


def train_model(repo, model_path):
    samples = repo.load_samples()
    if not samples:
        raise ValueError("no hay muestras guardadas")
    held_out = next(sample for sample in samples if sample[0] == TARGET)
    training = [sample for sample in samples if sample is not held_out]

    labels = [label for label, _ in training]
    features = [points for _, points in training]
    model = RandomForestClassifier(random_state=0).fit(features, labels)

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as file:
        pickle.dump(model, file)

    prediction = model.predict([held_out[1]])[0]
    return TrainingResult(recognized_a=prediction == TARGET)


def main():
    from dbConf.database import PostgresSampleRepository, connect_from_env

    if "DATABASE_URL" not in os.environ:
        print("Error: falta DATABASE_URL en el entorno o en .env", file=sys.stderr)
        sys.exit(1)

    conn = None
    try:
        conn = connect_from_env()
        result = train_model(PostgresSampleRepository(conn), MODEL_PATH)
    except Exception as error:
        print(f"Error: no se pudo entrenar el modelo: {error}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn is not None:
            conn.close()
    if result.recognized_a:
        print('La muestra de "a" fue reconocida como "a".')
    else:
        print('La muestra de "a" NO fue reconocida como "a".')


if __name__ == "__main__":
    main()
