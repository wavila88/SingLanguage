"""Entrena el modelo que reconoce frases en movimiento (hola, adios, gracias, numeros, nada...).

Este archivo es el "profesor": lee las grabaciones que guardaste en Neon, le enseña al modelo a
distinguirlas y guarda lo aprendido en un archivo (data/motion_phrases_model.pkl). Después,
recognize_message.py abre ese archivo y lo usa para reconocer en vivo; allí ya no se aprende nada.

Se ejecuta con:  python src/train/train_phrases.py
"""
import os
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path

# scikit-learn (se importa como "sklearn") es la librería que trae los algoritmos de aprendizaje.
# Usamos tres piezas suyas: un preparador de números, un algoritmo que aprende, y una tubería que
# las junta para que se comporten como un solo modelo.
from sklearn.linear_model import LogisticRegression  # el algoritmo que aprende a clasificar
from sklearn.pipeline import make_pipeline  # junta varias piezas en una sola "tubería"
from sklearn.preprocessing import StandardScaler  # pone todos los números en una escala parecida

# Este archivo se ejecuta como script, así que Python no sabe dónde está la carpeta src/.
# Se agrega para poder importar los demás módulos del proyecto (dataset.py, dbConf/...).
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# dataset.py convierte una grabación en una lista de números (ver motion_features allí).
# Es la MISMA función que usa recognize_message.py al reconocer: si el entrenamiento y el
# reconocimiento prepararan los números de forma distinta, el modelo no entendería lo que le llega.
from dataset import motion_features, normalize_phrase

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MOTION_MODEL_PATH = DATA_DIR / "motion_phrases_model.pkl"  # dónde se guarda el modelo entrenado
MIN_MOTION_FRAMES = 5  # una grabación con menos cuadros con mano es demasiado corta para aprender de ella


def _new_model():
    """Crea un modelo NUEVO y sin entrenar. Todavía no sabe nada de tus grabaciones.

    Es una tubería de dos pasos que se ejecutan en orden:

    1. StandardScaler: cada grabación es una lista de unos 300 números, y unos son muy grandes y otros
       muy pequeños (por ejemplo, la duración en segundos frente a una coordenada entre 0 y 1). Este
       paso los pone a todos en la misma escala, para que ninguno pese más solo por ser grande.
    2. LogisticRegression: el algoritmo que aprende. Para cada frase calcula una puntuación sumando los
       números de la grabación, cada uno multiplicado por un "peso". Aprender significa encontrar los
       pesos que hacen que la puntuación sea alta para la frase correcta y baja para las demás.
       Al final convierte las puntuaciones en porcentajes (la "confianza" que ves en pantalla).
       max_iter=2000 es cuántas vueltas puede dar ajustando los pesos antes de rendirse.
    """
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))


@dataclass
class TrainingResult:
    """Lo que devuelve el entrenamiento, para imprimirlo en pantalla."""

    kind: str
    phrases: dict  # frase -> (cuántas reconoció, cuántas había) cuando se deja cada grabación fuera a prueba
    skipped: int = 0  # grabaciones demasiado cortas que no se usaron


def _hold_out_each(features, labels):
    """Mide qué tan bien funciona el modelo, sin hacer trampa.

    Si le preguntáramos al modelo por las mismas grabaciones con las que aprendió, acertaría casi todo
    (como un alumno que ya vio las respuestas del examen) y eso no demostraría nada. Por eso se hace así:

        para cada grabación:
            1. se aparta esa grabación (el modelo no la ve)
            2. se entrena un modelo nuevo con TODAS las demás
            3. se le pregunta por la grabación apartada: ¿qué frase es?
            4. se anota si acertó

    Con 41 grabaciones se entrenan 41 modelos pequeños. Es lento pero justo, y funciona bien cuando
    hay pocas grabaciones (con muchas se usaría una parte fija para examen).
    """
    results = {}
    for index in range(len(labels)):
        # Todas las grabaciones menos la número `index`: [:index] es lo anterior, [index + 1:] lo posterior.
        training_features = features[:index] + features[index + 1:]
        training_labels = labels[:index] + labels[index + 1:]

        # .fit(...) es "aprender": recibe los ejemplos (números) y la respuesta correcta de cada uno
        # (el nombre de la frase), y ajusta los pesos hasta equivocarse lo menos posible.
        model = _new_model().fit(training_features, training_labels)

        # .predict(...) es "adivinar": le damos los números de una grabación que no vio
        # y nos devuelve el nombre de la frase que cree que es.
        guess = model.predict([features[index]])[0]

        phrase = labels[index]
        recognized, total = results.get(phrase, (0, 0))
        results[phrase] = (recognized + (guess == phrase), total + 1)  # True cuenta como 1, False como 0
    return results


def train_motion_model(repo, model_path):
    """Todo el entrenamiento, de principio a fin. Devuelve el resultado de la prueba."""
    # 1) Leer las grabaciones. `repo` es el acceso a la base de datos Neon (se inyecta desde main).
    #    Cada una llega como (nombre, lista de cuadros), y cada cuadro trae las manos que se vieron.
    samples = repo.load_motion_samples()

    # 2) Limpiar. "Hola" y "hola " son la misma frase (normalize_phrase quita espacios y mayúsculas)
    #    y se descartan las grabaciones demasiado cortas.
    usable = [(normalize_phrase(label), frames) for label, frames in samples if len(frames) >= MIN_MOTION_FRAMES]
    if not usable:
        raise ValueError("no hay grabaciones de movimiento")

    # 3) Convertir las grabaciones en el formato que entiende el modelo. Un modelo no sabe de manos ni
    #    de cámaras: solo recibe listas de números. Quedan dos listas paralelas:
    #      labels   = la respuesta correcta de cada grabación          ["hola", "adios", "hola", ...]
    #      features = sus números (por dónde pasó cada muñeca, etc.)    [[0.4, 0.5, ...], [...], ...]
    #    La grabación número 7 de `features` tiene su respuesta en la posición 7 de `labels`.
    labels = [label for label, _ in usable]
    features = [motion_features(frames) for _, frames in usable]

    # 4) Medir. Esto NO produce el modelo final: solo calcula el "N de M reconocidas" que se imprime.
    phrases = _hold_out_each(features, labels)

    # 5) Entrenar el modelo final con TODAS las grabaciones. Esta sí es la versión que se guarda.
    #    Se entrena aparte porque cuantos más ejemplos vea, mejor aprende.
    model = _new_model().fit(features, labels)

    # 6) Guardar. pickle convierte el modelo (los pesos aprendidos) en un archivo. Recognize_message.py
    #    lo abre con pickle.load y obtiene el mismo modelo, ya entrenado, sin tener que aprender otra vez.
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as file:
        pickle.dump(model, file)
    return TrainingResult("Movimiento", phrases, skipped=len(samples) - len(usable))


def format_result(result):
    """Convierte el resultado en las líneas de texto que se imprimen, por ejemplo: hola: 9 de 9 reconocidas."""
    lines = [f"{result.kind} · {phrase}: {recognized} de {total} reconocidas"
             for phrase, (recognized, total) in result.phrases.items()]
    if result.skipped:
        noun = "grabación omitida" if result.skipped == 1 else "grabaciones omitidas"
        lines.append(f"{result.kind}: {result.skipped} {noun} por tener menos de {MIN_MOTION_FRAMES} cuadros")
    return lines


def main():
    """Lo que ocurre al ejecutar el archivo: conectar con Neon, entrenar e imprimir el resultado."""
    # Este import está aquí dentro a propósito: así el entrenamiento en sí (arriba) no depende del
    # controlador de Postgres y se puede probar sin base de datos.
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
