import os
from io import BytesIO

import requests
import joblib


def descargar_modelo(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    return joblib.load(BytesIO(response.content))


# URLs de los modelos
MODEL_URL = os.getenv("MODEL_URL")
VECTORIZER_URL = os.getenv("VECTORIZER_URL")
ENCODER_URL = os.getenv("ENCODER_URL")


if not MODEL_URL or not VECTORIZER_URL or not ENCODER_URL:
    raise RuntimeError(
        "Faltan las variables de entorno MODEL_URL, "
        "VECTORIZER_URL o ENCODER_URL."
    )


# Descargar modelos desde OCI
modelo = descargar_modelo(MODEL_URL)
vectorizer = descargar_modelo(VECTORIZER_URL)
label_encoder = descargar_modelo(ENCODER_URL)


def limpiar_texto(texto):
    texto = texto.lower()
    texto = texto.strip()

    return texto


def clasificar_transaccion(descripcion):
    descripcion_limpia = limpiar_texto(descripcion)

    X = vectorizer.transform([descripcion_limpia])

    prediccion = modelo.predict(X)

    categoria = label_encoder.inverse_transform(prediccion)[0]

    return categoria