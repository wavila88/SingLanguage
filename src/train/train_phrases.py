import os
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dataset import motion_features, normalize_phrase

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MOTION_MODEL_PATH = DATA_DIR / "motion_phrases_model.pkl"
MIN_MOTION_FRAMES = 5


def _new_model():
    # Logistic regression gives much more confident probabilities than a forest when there are few recordings.
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))


@dataclass
class TrainingResult:
    kind: str
    phrases: dict  # phrase -> (recognized, total) when each of its samples is held out in turn
    skipped: int = 0


def _hold_out_each(features, labels):
    """Predict every sample with a model trained on all the others; count the hits per phrase."""
    results = {}
    for index in range(len(labels)):
        model = _new_model().fit(features[:index] + features[index + 1:], labels[:index] + labels[index + 1:])
        recognized, total = results.get(labels[index], (0, 0))
        hit = model.predict([features[index]])[0] == labels[index]
        results[labels[index]] = (recognized + hit, total + 1)
    return results


def train_motion_model(repo, model_path):
    samples = repo.load_motion_samples()
    usable = [(normalize_phrase(label), frames) for label, frames in samples if len(frames) >= MIN_MOTION_FRAMES]
    if not usable:
        raise ValueError("no hay grabaciones de movimiento")
    labels = [label for label, _ in usable]
    features = [motion_features(frames) for _, frames in usable]
    phrases = _hold_out_each(features, labels)

    model = _new_model().fit(features, labels)
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as file:
        pickle.dump(model, file)
    return TrainingResult("Movimiento", phrases, skipped=len(samples) - len(usable))


def format_result(result):
    lines = [f"{result.kind} · {phrase}: {recognized} de {total} reconocidas"
             for phrase, (recognized, total) in result.phrases.items()]
    if result.skipped:
        noun = "grabación omitida" if result.skipped == 1 else "grabaciones omitidas"
        lines.append(f"{result.kind}: {result.skipped} {noun} por tener menos de {MIN_MOTION_FRAMES} cuadros")
    return lines


def main():
    from dbConf.database import PostgresSampleRepository, connect_from_env

    if "DATABASE_URL" not in os.environ:
        print("Error: falta DATABASE_URL en el entorno o en .env", file=sys.stderr)
        sys.exit(1)

    conn = None
    try:
        conn = connect_from_env()
        result = train_motion_model(PostgresSampleRepository(conn), MOTION_MODEL_PATH)
    except Exception as error:
        print(f"Error: no se pudo entrenar el modelo: {error}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn is not None:
            conn.close()
    print("\n".join(format_result(result)))


if __name__ == "__main__":
    main()
