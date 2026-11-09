# SignLanguage - Detector de Vocales en Lenguaje de Señas

Proyecto progresivo en Python para aprender Visión por Computadora e Inteligencia Artificial detectando las vocales (A, E, I, O, U) en lenguaje de señas desde la cámara web.

## Ruta de Aprendizaje (Módulos / Specs)

1. **001 - Hola Mundo desde la Cámara (`001-camera-hello-world`)**: Abrir la cámara con OpenCV, mostrar el video en modo espejo, superponer texto en pantalla y cerrar con la tecla `q`.
2. **002 - Detección de Mano y Landmarks (`002-hand-landmarks`)**: Integrar MediaPipe Hands para detectar los 21 puntos clave de la mano en tiempo real y dibujarlos sobre el video.
3. **003 - Recolección de Datos (`003-dataset-collector`)**: Capturar y normalizar las coordenadas de los 21 puntos para cada vocal (A, E, I, O, U) y guardarlas en un archivo CSV.
4. **004 - Entrenamiento del Modelo (`004-model-training`)**: Entrenar y evaluar un clasificador con Scikit-Learn a partir del CSV y exportar el modelo entrenado.
5. **005 - Inferencia en Tiempo Real (`005-realtime-vowel-detection`)**: Conectar la cámara + MediaPipe + Modelo entrenado para mostrar en vivo la vocal detectada y su porcentaje de confianza.

## Estructura del Proyecto

- `src/` — Código fuente modular en Python.
- `tests/` — Pruebas automatizadas con `pytest`.
- `data/` — Datasets recolectados (`.csv`) y modelos entrenados (`.pkl`).

## Comandos

- Instalar dependencias: `pip install -r requirements.txt`
- Ejecutar aplicación: `python src/main.py`
- Ejecutar pruebas: `pytest`
