import pandas as pd

"""## Configuración y formato interno

Esta sección es el **único lugar** donde se indican los nombres de columnas que usa actualmente el análisis financiero (los mismos que usa el módulo de análisis de perfil financiero).

Si Backend cambia el nombre de alguna columna o el formato de los datos, normalmente solo hace falta modificar esta sección y la función `preparar_datos()`, sin tocar el resto del análisis.

Además, existe un módulo de transformación previo que garantiza que la columna de categoría solo llegue con un conjunto fijo de valores. Por eso el resto del análisis no necesita manejar categorías desconocidas.
"""

# Nombres de columnas que utiliza actualmente el análisis financiero
COLUMNA_USUARIO = "usuarioId"
COLUMNA_FECHA = "fecha"
COLUMNA_TIPO = "tipo"
COLUMNA_CANTIDAD = "monto"
COLUMNA_CATEGORIA = "categoria"

# Valores que puede tomar la columna Tipo en el dataset actual
# (importante: están en inglés porque así los definió el dataset original)
VALOR_TIPO_INGRESO = "INGRESO"
VALOR_TIPO_GASTO = "GASTO"

# Categorías válidas de gasto. Un módulo de transformación previo ya
# garantiza que solo lleguen estas categorías, por lo que el resto del
# análisis puede asumir que categoria_principal siempre será una de estas.
CATEGORIAS_VALIDAS = [
    "Alimentación",
    "Transporte",
    "Salud",
    "Vivienda",
    "Educación",
    "Ocio",
    "Servicios",
    "Compras",
    "Otros",
]

"""## Preparación de datos — `preparar_datos()`

Esta función es la **capa de adaptación** entre lo que envíe Backend y el formato interno que necesita el resto del análisis. Hace 4 cosas, en este orden:

1. Detecta el formato de entrada y lo convierte al formato interno.
2. Valida que estén las columnas mínimas necesarias (`validar_datos()`).
3. Procesa la Fecha **solo si está presente** (es un campo opcional).
4. Devuelve el DataFrame ya preparado.

Por ahora solo sabe convertir DataFrame o lista de diccionarios en el formato interno actual (`usuario_id`, `Fecha`, `Tipo`, `Cantidad`, `Categoria`). Si Backend termina enviando otro formato (por ejemplo el JSON de NoCountry), el paso 1 es el único lugar que habría que ampliar.
"""

def validar_datos(datos_preparados):
    """
    Comprueba que el DataFrame preparado tenga las columnas mínimas que
    necesita el análisis. Si falta alguna, lanza un error con un mensaje
    fácil de entender en vez de un error técnico de pandas.

    COLUMNA_FECHA y COLUMNA_USUARIO no se validan aquí porque ninguna
    métrica actual depende de ellas: Fecha es opcional y usuario_id solo
    se usa como identificador, no en los cálculos.
    """
    columnas_obligatorias = [COLUMNA_CANTIDAD, COLUMNA_TIPO, COLUMNA_CATEGORIA]

    for columna in columnas_obligatorias:
        if columna not in datos_preparados.columns:
            raise ValueError(
                f"Falta la columna '{columna}'. Revisa preparar_datos() "
                f"para adaptar el formato de entrada."
            )

def preparar_datos(datos):
    """
    Recibe los datos de entrada (lista de diccionarios o DataFrame) con las
    transacciones de un usuario y los convierte al formato interno estándar
    que utiliza el resto del análisis.

    Este es el punto de adaptación de los datos de entrada. Si Backend
    cambia el formato en el futuro, esta es la función que hay que modificar.
    """
    # 1. Detectar el formato de entrada y convertirlo al formato interno.
    #    Por ahora se soportan DataFrame o lista de diccionarios ya en el
    #    formato interno (usuario_id, Fecha, Tipo, Cantidad, Categoria).
    #    Si en el futuro Backend envía otro formato (por ejemplo el JSON
    #    de NoCountry con "ingreso_mensual" y "transacciones"), aquí es
    #    donde habría que agregar la conversión hacia este mismo formato
    #    interno, antes de continuar con los pasos siguientes.
    if isinstance(datos, pd.DataFrame):
        datos_preparados = datos.copy()
    else:
        datos_preparados = pd.DataFrame(datos)

    # 2. Validar que estén las columnas mínimas necesarias
    validar_datos(datos_preparados)

    # 3. La Fecha es un campo opcional. Ninguna métrica actual la utiliza,
    #    así que si no viene, la función no debe fallar por eso. Si viene,
    #    se convierte a datetime para dejarla lista por si en el futuro
    #    se agrega alguna métrica que sí la necesite.
    if COLUMNA_FECHA in datos_preparados.columns:
        datos_preparados[COLUMNA_FECHA] = pd.to_datetime(datos_preparados[COLUMNA_FECHA])

    # 4. Devolvemos el DataFrame ya preparado
    return datos_preparados

"""### ¿Cómo adaptar los datos de Backend?

Algunos ejemplos concretos de qué hacer si el formato de entrada cambia:

**Caso 1 — Backend cambia el nombre de un campo (por ejemplo `"Cantidad"` pasa a llamarse `"valor"`)**

Solo hay que cambiar la sección de configuración (sección 3):

```python
COLUMNA_CANTIDAD = "valor"
```

No hace falta tocar `preparar_datos()` ni ninguna otra función.

**Caso 2 — Backend no manda Fecha**

No pasa nada: `preparar_datos()` ya trata la Fecha como opcional y el resto del análisis (métricas, Scores, Financial Score, perfil, recomendaciones) **no utiliza la Fecha en ningún cálculo actual**, así que el análisis puede funcionar sin ella sin revisar nada más.

**Caso 3 — Backend manda el formato de NoCountry** (`ingreso_mensual`, `transacciones` con `descripcion` y `valor`)

Este formato es distinto al interno, así que habría que agregar la conversión dentro del paso 1 de `preparar_datos()`: por ejemplo, convertir `ingreso_mensual` en una fila con `Tipo = VALOR_TIPO_INGRESO`, y cada elemento de `transacciones` en una fila con `Tipo = VALOR_TIPO_GASTO`, `Cantidad = valor` y `Categoria` según corresponda. Esto **todavía no está implementado** porque no es el formato definitivo confirmado por Backend; se deja indicado aquí como referencia.

**Caso 4 — Backend solo manda gastos, sin ingresos**

Las reglas actuales de `tasa_ahorro`, `ratio_gasto`, `score_ahorro` y `score_gasto` necesitan ingresos para calcularse correctamente. Si no hay ingresos, `calcular_metricas()` (sección 5) **no inventa un valor de 0**: lanza un error explicando que faltan los ingresos, para que se resuelva explícitamente con Backend en vez de dar un resultado incorrecto en silencio.

## 5. Cálculo de métricas — `calcular_metricas()`

Aplica las mismas fórmulas que el módulo de análisis de perfil financiero, pero para un solo usuario a la vez (en vez de agrupar por `usuario_id`, ya que aquí los datos ya vienen filtrados a un único usuario).
"""

def calcular_metricas(datos_preparados):
    """
    Recibe el DataFrame en formato interno con las transacciones de un
    usuario y calcula las métricas financieras necesarias para el resto
    del análisis (ingresos, gastos, ahorro, categoría principal, etc.).

    Devuelve un diccionario con todas las métricas calculadas.

    Lanza un ValueError si no hay suficientes datos de ingresos, ya que
    sin ingresos no se puede calcular tasa_ahorro ni ratio_gasto.
    """
    # Separamos ingresos y gastos, igual que en el módulo original
    ingresos = datos_preparados[datos_preparados[COLUMNA_TIPO] == VALOR_TIPO_INGRESO]
    gastos = datos_preparados[datos_preparados[COLUMNA_TIPO] == VALOR_TIPO_GASTO]

    # Total de ingresos y de gastos
    total_ingresos = ingresos[COLUMNA_CANTIDAD].sum()
    total_gastos = gastos[COLUMNA_CANTIDAD].sum()

    # Sin ingresos no se puede calcular correctamente tasa_ahorro,
    # ratio_gasto, score_ahorro ni score_gasto. En vez de inventar un
    # ingreso o reemplazarlo por 0, se detiene el cálculo con un mensaje
    # claro para resolverlo explícitamente con Backend.
    if total_ingresos <= 0:
        raise ValueError(
            "No se encontraron ingresos suficientes (Tipo == "
            f"'{VALOR_TIPO_INGRESO}') para calcular tasa_ahorro, ratio_gasto, "
            "score_ahorro y score_gasto. Revisa cómo Backend está enviando "
            "los ingresos antes de continuar; no se debe inventar este dato."
        )

    # Número total de transacciones (ingresos + gastos)
    num_transacciones = len(datos_preparados)

    # Gasto promedio y gasto máximo
    if len(gastos) > 0:
        gasto_promedio = gastos[COLUMNA_CANTIDAD].mean()
        gasto_maximo = gastos[COLUMNA_CANTIDAD].max()
    else:
        gasto_promedio = 0
        gasto_maximo = 0

    # Número de categorías distintas en las que el usuario gastó
    num_categorias = gastos[COLUMNA_CATEGORIA].nunique()

    # Ahorro = ingresos - gastos
    ahorro = total_ingresos - total_gastos

    # Tasa de ahorro y ratio gasto/ingreso
    # (ya sabemos que total_ingresos > 0 por la validación anterior)
    tasa_ahorro = ahorro / total_ingresos
    ratio_gasto = total_gastos / total_ingresos

    # Frecuencia de gastos = número de transacciones de tipo gasto
    frecuencia_gastos = len(gastos)

    # Categoría principal de gasto y su porcentaje sobre el total gastado
    if len(gastos) > 0:
        gasto_por_categoria = gastos.groupby(COLUMNA_CATEGORIA)[COLUMNA_CANTIDAD].sum()
        categoria_principal = gasto_por_categoria.idxmax()
        porcentaje_categoria_principal = (gasto_por_categoria.max() / total_gastos) * 100
    else:
        categoria_principal = "Otros"
        porcentaje_categoria_principal = 0

    # Armamos el diccionario final de métricas
    metricas = {
        "total_ingresos": total_ingresos,
        "total_gastos": total_gastos,
        "num_transacciones": num_transacciones,
        "gasto_promedio": gasto_promedio,
        "gasto_maximo": gasto_maximo,
        "num_categorias": num_categorias,
        "ahorro": ahorro,
        "tasa_ahorro": tasa_ahorro,
        "ratio_gasto": ratio_gasto,
        "frecuencia_gastos": frecuencia_gastos,
        "categoria_principal": categoria_principal,
        "porcentaje_categoria_principal": porcentaje_categoria_principal,
    }

    return metricas

"""## Cálculo de Scores

Se mantienen exactamente las mismas reglas de puntuación que el módulo de análisis de perfil financiero. Cada regla vive en su propia función, así que si durante el hackathon cambia algún rango, solo hay que editar la función correspondiente.
"""

def calcular_score_ahorro(tasa_ahorro):
    """
    Recibe la tasa de ahorro del usuario y devuelve la puntuación
    correspondiente (0 a 35 puntos).
    """
    if tasa_ahorro >= 0.40:
        return 35
    elif tasa_ahorro >= 0.20:
        return 28
    elif tasa_ahorro >= 0.10:
        return 18
    elif tasa_ahorro >= 0:
        return 8
    else:
        return 0


def calcular_score_gasto(ratio_gasto):
    """
    Recibe el ratio gasto/ingreso del usuario y devuelve la puntuación
    correspondiente (0 a 30 puntos).
    """
    if ratio_gasto <= 0.50:
        return 30
    elif ratio_gasto <= 0.70:
        return 24
    elif ratio_gasto <= 0.90:
        return 18
    elif ratio_gasto <= 1.00:
        return 10
    else:
        return 0


def calcular_score_diversificacion(num_categorias):
    """
    Recibe el número de categorías de gasto del usuario y devuelve la
    puntuación correspondiente (5 a 20 puntos).
    """
    if num_categorias >= 8:
        return 20
    elif num_categorias >= 5:
        return 15
    elif num_categorias >= 3:
        return 10
    else:
        return 5


def calcular_score_frecuencia(frecuencia_gastos):
    """
    Recibe la frecuencia de gastos del usuario y devuelve la puntuación
    correspondiente (0 a 15 puntos).
    """
    if frecuencia_gastos <= 10:
        return 15
    elif frecuencia_gastos <= 20:
        return 12
    elif frecuencia_gastos <= 30:
        return 8
    elif frecuencia_gastos <= 40:
        return 4
    else:
        return 0


def calcular_scores(metricas):
    """
    Recibe el diccionario de métricas y calcula los 4 Scores financieros.
    Devuelve un diccionario con los 4 Scores.
    """
    score_ahorro = calcular_score_ahorro(metricas["tasa_ahorro"])
    score_gasto = calcular_score_gasto(metricas["ratio_gasto"])
    score_diversificacion = calcular_score_diversificacion(metricas["num_categorias"])
    score_frecuencia = calcular_score_frecuencia(metricas["frecuencia_gastos"])

    scores = {
        "score_ahorro": score_ahorro,
        "score_gasto": score_gasto,
        "score_diversificacion": score_diversificacion,
        "score_frecuencia": score_frecuencia,
    }

    return scores

"""## Financial Score — `calcular_financial_score()`"""

def calcular_financial_score(scores):
    """
    Recibe el diccionario de los 4 Scores y devuelve el Financial Score
    final, que es simplemente la suma de los 4 (máximo 100 puntos).
    """
    financial_score = (
        scores["score_ahorro"]
        + scores["score_gasto"]
        + scores["score_diversificacion"]
        + scores["score_frecuencia"]
    )

    return financial_score

"""## Perfil financiero — `obtener_perfil_financiero()`"""

def obtener_perfil_financiero(financial_score):
    """
    Recibe el Financial Score y devuelve el perfil financiero
    correspondiente: "Saludable", "En observación" o "En riesgo".
    """
    if financial_score >= 70:
        return "Saludable"
    elif financial_score >= 40:
        return "En observación"
    else:
        return "En riesgo"

"""## Recomendaciones

Esta sección reutiliza tal cual la lógica de `modulo3_recomendaciones_financieras.ipynb`: los mismos diccionarios de texto y las mismas funciones, sin cambiar ninguna recomendación.

`recomendaciones_categoria` tiene una entrada para cada una de las categorías listadas en `CATEGORIAS_VALIDAS` (sección 3), así que siempre habrá una recomendación disponible para la categoría principal que llegue.
"""

# Recomendación según el score con menor puntaje
recomendaciones_score = {
    "score_ahorro": "Intenta destinar una parte de tus ingresos al ahorro cada mes. Incluso pequeñas cantidades pueden ayudarte a construir una mayor estabilidad financiera y afrontar imprevistos.",
    "score_gasto": "Revisa tus gastos del mes y prioriza aquellos que realmente sean necesarios. Un mejor control de tus gastos puede ayudarte a aprovechar mejor tus ingresos.",
    "score_diversificacion": "La mayor parte de tus gastos está concentrada en pocas categorías. Distribuir mejor tu presupuesto puede ayudarte a mantener unas finanzas más equilibradas.",
    "score_frecuencia": "Se detectó una alta frecuencia de compras. Antes de realizar una compra, pregúntate si realmente la necesitas o si puede esperar.",
}

# Recomendación según la categoría principal de gasto
recomendaciones_categoria = {
    "Alimentación": "Planificar mejor tus compras puede ayudarte a ahorrar sin afectar tu alimentación.",
    "Compras": "Antes de realizar una compra, pregúntate si realmente la necesitas o si puede esperar.",
    "Transporte": "Evalúa alternativas de transporte que te permitan reducir este gasto cuando sea posible.",
    "Servicios": "Revisa los servicios y suscripciones que pagas cada mes. Es posible que alguno ya no sea necesario.",
    "Ocio": "Disfrutar de tu tiempo libre es importante, pero reducir un poco este tipo de gastos puede ayudarte a aumentar tu capacidad de ahorro.",
    "Vivienda": "Revisa periódicamente los gastos relacionados con tu vivienda para identificar oportunidades de ahorro.",
    "Salud": "Mantener un presupuesto destinado al cuidado de tu salud también forma parte de una buena planificación financiera.",
    "Educación": "Continuar invirtiendo en educación es positivo, procurando siempre mantener un presupuesto equilibrado.",
    "Otros": "Revisa los movimientos clasificados como \"Otros\" para comprender mejor en qué estás utilizando tu dinero.",
}

# Recomendación según el perfil financiero
recomendaciones_perfil = {
    "Saludable": "¡Vas por buen camino! Sigue manteniendo el hábito de ahorrar cada mes.",
    "En observación": "Tus finanzas son estables, pero todavía existen oportunidades para mejorar. Continúa fortaleciendo tus hábitos de ahorro y planificación.",
    "En riesgo": "Tu situación financiera requiere mayor atención. Organiza un presupuesto mensual y prioriza tus gastos más importantes para recuperar el equilibrio financiero.",
}

def obtener_recomendacion_score(datos):
    """
    Compara los scores de ahorro, gasto, diversificación y frecuencia,
    y devuelve la recomendación correspondiente al que tenga el menor valor.

    En caso de empate, se prioriza en este orden:
    score_ahorro > score_gasto > score_diversificacion > score_frecuencia
    """
    orden_prioridad = ["score_ahorro", "score_gasto", "score_diversificacion", "score_frecuencia"]

    valores_scores = {
        "score_ahorro": datos["score_ahorro"],
        "score_gasto": datos["score_gasto"],
        "score_diversificacion": datos["score_diversificacion"],
        "score_frecuencia": datos["score_frecuencia"],
    }

    score_menor = None
    valor_menor = None

    for nombre_score in orden_prioridad:
        valor_actual = valores_scores[nombre_score]
        if valor_menor is None or valor_actual < valor_menor:
            valor_menor = valor_actual
            score_menor = nombre_score

    return recomendaciones_score[score_menor]


def obtener_recomendacion_categoria(datos):
    """
    Devuelve la recomendación correspondiente a la categoría principal
    de gasto del usuario.
    """
    categoria = datos["categoria_principal"]
    return recomendaciones_categoria[categoria]


def obtener_recomendacion_perfil(datos):
    """
    Devuelve la recomendación correspondiente al perfil financiero
    del usuario.
    """
    perfil = datos["perfil_financiero"]
    return recomendaciones_perfil[perfil]


def generar_recomendaciones(datos):
    """
    Recibe un diccionario con financial_score, perfil_financiero y los
    4 Scores, categoria_principal y porcentaje_categoria_principal, y
    devuelve una lista con exactamente 3 recomendaciones.
    """
    recomendacion_1 = obtener_recomendacion_score(datos)
    recomendacion_2 = obtener_recomendacion_categoria(datos)
    recomendacion_3 = obtener_recomendacion_perfil(datos)

    lista_recomendaciones = [recomendacion_1, recomendacion_2, recomendacion_3]

    return lista_recomendaciones

"""## 10. Función principal — `analizar_finanzas()`

Esta es la función que usará Backend. Solo coordina las funciones anteriores, no contiene lógica nueva.
"""

def analizar_finanzas(datos):
    """
    Función principal del módulo de integración.

    Recibe las transacciones de un usuario (en el formato que llegue de
    Backend) y devuelve un diccionario con el Financial Score, el Perfil
    Financiero, los 4 Scores, la categoría principal y las 3
    recomendaciones financieras.

    Backend solo necesita conocer esta función; el resto son funciones
    internas del módulo.
    """
    # 1. Preparamos los datos al formato interno estándar
    datos_preparados = preparar_datos(datos)

    # 2. Calculamos las métricas financieras
    metricas = calcular_metricas(datos_preparados)

    # 3. Calculamos los 4 Scores
    scores = calcular_scores(metricas)

    # 4. Calculamos el Financial Score
    financial_score = calcular_financial_score(scores)

    # 5. Obtenemos el perfil financiero
    perfil_financiero = obtener_perfil_financiero(financial_score)

    # 6. Armamos el diccionario que necesita el módulo de recomendaciones
    datos_para_recomendaciones = {
        "financial_score": financial_score,
        "perfil_financiero": perfil_financiero,
        "score_ahorro": scores["score_ahorro"],
        "score_gasto": scores["score_gasto"],
        "score_diversificacion": scores["score_diversificacion"],
        "score_frecuencia": scores["score_frecuencia"],
        "categoria_principal": metricas["categoria_principal"],
        "porcentaje_categoria_principal": metricas["porcentaje_categoria_principal"],
    }

    # 7. Generamos las 3 recomendaciones
    recomendaciones = generar_recomendaciones(datos_para_recomendaciones)

    # 8. Construimos el resultado final
    resultado = {
        "financial_score": financial_score,
        "perfil_financiero": perfil_financiero,
        "score_ahorro": scores["score_ahorro"],
        "score_gasto": scores["score_gasto"],
        "score_diversificacion": scores["score_diversificacion"],
        "score_frecuencia": scores["score_frecuencia"],
        "categoria_principal": metricas["categoria_principal"],
        "porcentaje_categoria_principal": metricas["porcentaje_categoria_principal"],
        "recomendaciones": recomendaciones,
    }

    return resultado