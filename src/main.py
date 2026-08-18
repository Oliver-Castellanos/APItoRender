from fastapi import FastAPI
from pydantic import BaseModel

from src.predict import clasificar_transaccion


# ==========================
# Crear aplicación
# ==========================

app = FastAPI(
    title="API de Clasificación de Transacciones",
    description="API para clasificar descripciones de transacciones financieras.",
    version="1.0.0"
)


# ==========================
# Modelo de entrada
# ==========================

class Transaccion(BaseModel):
    descripcion: str


# ==========================
# Endpoint raíz
# ==========================

@app.get("/")
def root():
    return {
        "mensaje": "API de clasificación de transacciones funcionando"
    }


# ==========================
# Health check
# ==========================

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ==========================
# Predicción
# ==========================

@app.post("/predict")
def predict(transaccion: Transaccion):

    categoria = clasificar_transaccion(
        transaccion.descripcion
    )

    return {
        "descripcion": transaccion.descripcion,
        "categoria": categoria
    }