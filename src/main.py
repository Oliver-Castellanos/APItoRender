from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from src.predict import clasificar_transaccion
from src.analisis_financiero import analizar_finanzas


app = FastAPI(
    title="API Finanzas",
    description="API para clasificación de transacciones y análisis financiero",
    version="1.0.0"
)


# ============================================================
# MODELOS PARA /predict
# ============================================================

class TransaccionPredict(BaseModel):
    descripcion: str


# ============================================================
# MODELOS PARA /analizar-finanzas
# ============================================================

class TransaccionFinanciera(BaseModel):
    usuarioId: Optional[str] = None
    fecha: Optional[str] = None
    tipo: str
    monto: float
    categoria: str


class AnalisisFinancieroRequest(BaseModel):
    transacciones: List[TransaccionFinanciera]


# ============================================================
# ENDPOINT PRINCIPAL
# ============================================================

@app.get("/")
def root():
    return {
        "mensaje": "API de Finanzas funcionando",
        "endpoints": [
            "/predict",
            "/analizar-finanzas",
            "/docs"
        ]
    }


# ============================================================
# CLASIFICACIÓN DE TRANSACCIONES
# ============================================================

@app.post("/predict")
def predict(transaccion: TransaccionPredict):
    try:
        categoria = clasificar_transaccion(
            transaccion.descripcion
        )

        return {
            "descripcion": transaccion.descripcion,
            "categoria": categoria
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al clasificar la transacción: {str(e)}"
        )


# ============================================================
# ANÁLISIS FINANCIERO
# ============================================================

@app.post("/analizar-finanzas")
def analizar_finanzas_endpoint(
    request: AnalisisFinancieroRequest
):
    try:

        # Convertimos los objetos Pydantic a diccionarios
        transacciones = [
            transaccion.model_dump()
            for transaccion in request.transacciones
        ]

        # Ejecutamos todo el análisis financiero
        resultado = analizar_finanzas(transacciones)

        return resultado

    except ValueError as e:
        # Errores esperados relacionados con los datos,
        # por ejemplo, que no existan ingresos.
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        # Errores inesperados
        raise HTTPException(
            status_code=500,
            detail=f"Error al analizar las finanzas: {str(e)}"
        )
