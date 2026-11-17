"""Medición reproducible de tiempo y memoria, y comparación de implementaciones (Fase 3).

Reglas de medición del curso (Apunte de la Fase 3, sección 4):
1. Repetir y conservar el MÍNIMO: los valores altos reflejan interferencia del sistema operativo,
   no el costo del código (`timeit.repeat`).
2. Medir sobre el tamaño de trabajo (26.180 glaciares) y sobre tamaños crecientes, para ver cómo
   crece el costo y no solo un punto.
3. Verificar equivalencia antes de comparar: dos implementaciones solo son comparables si
   producen el mismo resultado. `comparar` lo comprueba y se detiene si no.

Método formal: `exponente_empirico` ajusta log(t) = a + b·log(n) por mínimos cuadrados. La
pendiente b estima el orden de crecimiento (b ≈ 1 lineal, b ≈ 2 cuadrático) y se contrasta con
la complejidad teórica declarada para cada implementación.

Las implementaciones alternativas viven aquí y no en los módulos de producción: concentracion.py,
limpieza.py y metadatos.py conservan solo la versión elegida.
"""

import gc
import timeit
import tracemalloc

import numpy as np
import pandas as pd

import utilidades as utl


# ======================================================================== medición
def medir(funcion, *args, repeticiones=5, **kwargs):
    """Tiempo mínimo de `repeticiones` ejecuciones (s) y memoria pico de una ejecución (MB).

    La memoria se mide en una ejecución aparte: tracemalloc agrega costo y alteraría el tiempo.
    """
    if repeticiones < 1:
        raise ValueError("repeticiones debe ser ≥ 1")
    llamada = lambda: funcion(*args, **kwargs)                               # noqa: E731
    gc.collect()
    tiempos = timeit.repeat(llamada, number=1, repeat=repeticiones)
    tracemalloc.start()
    try:
        resultado = llamada()
        _, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return {"segundos": min(tiempos), "segundos_mediana": float(np.median(tiempos)),
            "memoria_mb": pico / 1024**2, "resultado": resultado}


def son_equivalentes(a, b, tolerancia=1e-9):
    """Compara resultados de distintos tipos: números, arreglos, Series, DataFrame o dict."""
    if isinstance(a, pd.DataFrame):
        return a.equals(b)
    if isinstance(a, pd.Series):
        return a.equals(b)
    if isinstance(a, dict):
        return a == b and list(a) == list(b)                                  # mismo orden de claves
    return bool(np.allclose(a, b, rtol=tolerancia, atol=tolerancia))


def comparar(implementaciones, entradas, repeticiones=5, equivalentes=son_equivalentes):
    """Mide cada implementación sobre cada entrada después de verificar que coinciden.

    implementaciones : {nombre: función(entrada)}
    entradas         : {tamaño n: entrada}
    Devuelve una fila por (n, implementación) con tiempo mínimo, memoria pico y razón respecto
    de la más rápida para ese n. Lanza ProyectoError si dos implementaciones difieren.
    """
    filas = []
    for n, entrada in entradas.items():
        medidas = {nombre: medir(funcion, entrada, repeticiones=repeticiones)
                   for nombre, funcion in implementaciones.items()}
        referencia_nombre, referencia = next(iter(medidas.items()))
        for nombre, medida in medidas.items():
            if not equivalentes(referencia["resultado"], medida["resultado"]):
                raise utl.ProyectoError(f"n = {n}: {nombre} no da el mismo resultado que {referencia_nombre}")
        minimo = min(m["segundos"] for m in medidas.values())
        for nombre, medida in medidas.items():
            filas.append({"n": n, "implementacion": nombre, "ms": 1000 * medida["segundos"],
                          "memoria_mb": medida["memoria_mb"], "veces_la_mas_rapida": medida["segundos"] / minimo})
    return pd.DataFrame(filas)


def exponente_empirico(tabla):
    """Pendiente b de log(ms) = a + b·log(n) por implementación (orden de crecimiento observado)."""
    filas = []
    for nombre, grupo in tabla.groupby("implementacion", sort=False):
        if grupo["n"].nunique() < 2:
            raise ValueError(f"{nombre}: se necesitan al menos dos tamaños para estimar el exponente")
        b, _ = np.polyfit(np.log(grupo["n"]), np.log(grupo["ms"]), 1)
        filas.append({"implementacion": nombre, "exponente_tiempo": round(float(b), 2)})
    return pd.DataFrame(filas)


def muestras(serie, tamanos, semilla=utl.SEMILLA):
    """{n: arreglo} con muestras con reemplazo de `serie`, reproducibles por la semilla."""
    generador = np.random.default_rng(semilla)
    valores = np.asarray(serie, dtype=float)
    return {n: generador.choice(valores, size=n, replace=True) for n in tamanos}


# ====================================================== 1. Gini: tres implementaciones
def gini_pares_matriz(x):
    """Definición: Σᵢ Σⱼ |xᵢ − xⱼ| / (2 n² x̄) con una matriz n × n. Tiempo O(n²), memoria O(n²)."""
    x = np.asarray(x, dtype=float)
    return float(np.abs(x[:, None] - x[None, :]).sum() / (2 * len(x) ** 2 * x.mean()))


def gini_pares_bucle(x):
    """La misma definición recorriendo una fila a la vez. Tiempo O(n²), memoria O(n)."""
    x = np.asarray(x, dtype=float)
    total = 0.0
    for valor in x:
        total += np.abs(x - valor).sum()
    return float(total / (2 * len(x) ** 2 * x.mean()))


def gini_ordenado(x):
    """Fórmula sobre los valores ordenados (la de concentracion.IndiceGini). Tiempo O(n log n), memoria O(n)."""
    import concentracion as con
    return con.IndiceGini().calcular(x)


# =========================================== 2. Participación de los mayores: tres formas
def participacion_nlargest(x, fraccion=0.01):
    """Como en F2 (sección 2.2.1): pandas nlargest. O(n log k) con k = n·fracción."""
    serie = pd.Series(x)
    k = int(len(serie) * fraccion)
    return float(100 * serie.nlargest(k).sum() / serie.sum())


def participacion_orden_total(x, fraccion=0.01):
    """Ordena todo el arreglo y suma la cola. O(n log n)."""
    x = np.sort(np.asarray(x, dtype=float))
    k = int(len(x) * fraccion)
    return float(100 * x[len(x) - k:].sum() / x.sum())


def participacion_particion(x, fraccion=0.01):
    """Selección parcial con np.partition (la de concentracion.ParticipacionMayores). O(n)."""
    import concentracion as con
    return con.ParticipacionMayores(fraccion).calcular(x)


# ================================== 3. Normalización del texto (paso NormalizadorTexto)
def normalizar_fila_a_fila(serie):
    """La versión de F2 (línea base): repara y normaliza cada uno de los n valores, aunque se
    repitan. O(n) llamadas a la normalización."""
    import limpieza as lim
    return serie.map(lambda v: v if pd.isna(v) else " ".join(lim.reparar_codificacion(v).upper().split()))


def normalizar_por_valores_unicos(serie):
    """La adoptada en limpieza.normalizar_texto: normaliza los u valores distintos una vez y los
    asigna con un diccionario. O(u) llamadas + O(n) búsquedas en el diccionario.

    Columnas como REGION (16 valores) o FUENTE_DIG (19) repiten el mismo texto miles de veces:
    calcularlo una vez y guardarlo evita repetir trabajo.
    """
    import limpieza as lim
    return lim.normalizar_texto(serie)


# ============================================================== 4. Recursión vs. pila
def aplanar_recursivo(estructura):
    import metadatos as md
    return md.aplanar(estructura)


def aplanar_con_pila(estructura):
    import metadatos as md
    return md.aplanar_iterativo(estructura)
