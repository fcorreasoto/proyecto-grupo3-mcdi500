"""Funciones de limpieza y codificación del inventario (programación estructurada).

Son las funciones de F2 (secciones 2 a 4) trasladadas sin cambios de lógica, para que las
clases de `transformadores.py` las reutilicen en vez de copiarlas. Cada función recibe datos,
devuelve un resultado nuevo y no modifica su entrada: no guarda estado entre llamadas, por eso
son funciones y no clases.
"""

import re
import unicodedata

import numpy as np
import pandas as pd

MOJIBAKE = re.compile("[├┤│ÃÂ]")   # señales de UTF-8 leído como CP437
ANGULOS = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SW": 225, "W": 270, "NW": 315}


# ------------------------------------------------------------------ perfil y columnas
def perfil_columnas(df):
    """Tipo, no nulos, faltantes y valores únicos de cada columna."""
    return pd.DataFrame({
        "variable": df.columns,
        "tipo": [str(df[c].dtype) for c in df.columns],
        "no_nulos": [int(df[c].notna().sum()) for c in df.columns],
        "pct_faltante": [round(df[c].isna().mean() * 100, 2) for c in df.columns],
        "valores_unicos": [int(df[c].nunique(dropna=True)) for c in df.columns],
    })


def columnas_sin_informacion(df, umbral_faltantes=0.60):
    """Columnas con más faltantes que el umbral o con un único valor observado."""
    filas = []
    for columna in df.columns:
        pct = df[columna].isna().mean()
        unicos = df[columna].nunique(dropna=True)
        if pct > umbral_faltantes or unicos <= 1:
            filas.append({"variable": columna, "pct_faltante": round(pct * 100, 2), "valores_unicos": unicos,
                          "motivo": f"faltantes > {umbral_faltantes:.0%}" if pct > umbral_faltantes else "valor único",
                          "valor_observado": df[columna].dropna().iloc[0] if unicos == 1 else None})
    return pd.DataFrame(filas, columns=["variable", "pct_faltante", "valores_unicos", "motivo", "valor_observado"])


def columnas_texto(df, excluir=()):
    """Columnas de texto con al menos un dato, salvo las de `excluir`."""
    return [c for c in df.columns
            if pd.api.types.is_string_dtype(df[c]) and df[c].notna().any() and c not in excluir]


def eliminar_columnas(df, columnas):
    """Devuelve una copia sin las columnas indicadas; falla si alguna no existe."""
    faltan = set(columnas) - set(df.columns)
    if faltan:
        raise KeyError(f"Columnas inexistentes: {sorted(faltan)}")
    return df.drop(columns=list(columnas))


# ----------------------------------------------------------------------------- texto
def reparar_codificacion(texto):
    """Revierte UTF-8 leído como CP437 solo si hay señales de codificación rota."""
    if not MOJIBAKE.search(texto):
        return texto
    try:
        return texto.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto


def _normalizar_valor(valor):
    return " ".join(reparar_codificacion(valor).upper().split())


def normalizar_texto(serie):
    """Repara la codificación, pasa a mayúsculas y colapsa espacios; los nulos se mantienen.

    Optimización de F3: normaliza solo los valores distintos y los asigna con un diccionario. Las
    columnas de texto repiten pocos valores miles de veces (REGION tiene 16 en 26.180 filas), y
    medicion.py midió esta versión entre 1,3 y 2,5 veces más rápida que la de F2, que normalizaba
    fila a fila, con la mitad de memoria y el mismo resultado.
    """
    tabla = {valor: _normalizar_valor(valor) for valor in serie.dropna().unique()}
    return serie.map(lambda v: v if pd.isna(v) else tabla[v])


def clave_texto(valor):
    """Clave de comparación: sin tildes, en mayúsculas y con espacios simples."""
    sin_tildes = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.upper().split())


# ----------------------------------------------------------------------------- tipos
def convertir_decimal_coma(serie):
    """'-18,17' (texto) → -18.17 (float); lo no interpretable queda como NaN."""
    return pd.to_numeric(serie.astype("string").str.strip().str.replace(",", ".", regex=False), errors="coerce")


def parsear_fecha_mixta(serie):
    """Devuelve (fecha, año): DD/MM/AAAA, luego MM/DD/AAAA; 'AAAA' solo aporta el año."""
    texto = serie.astype("string").str.strip()
    dia_mes = pd.to_datetime(texto, format="%d/%m/%Y", errors="coerce")
    mes_dia = pd.to_datetime(texto, format="%m/%d/%Y", errors="coerce")
    fecha = dia_mes.fillna(mes_dia)
    solo_anio = pd.to_numeric(texto.where(texto.str.fullmatch(r"\d{4}").fillna(False)), errors="coerce")
    anio = fecha.dt.year.astype("Int64").fillna(solo_anio.astype("Int64"))
    return fecha, anio


# ----------------------------------------------------------------------- categorías
def categorias_raras(serie, umbral=0.01):
    """Categorías cuya frecuencia relativa es menor que `umbral`, ordenadas."""
    frecuencia = serie.value_counts(normalize=True)
    return sorted(frecuencia[frecuencia < umbral].index)


def agrupar_categorias(serie, raras, etiqueta="OTRAS"):
    """Reemplaza por `etiqueta` las categorías listadas en `raras`."""
    return serie.where(~serie.isin(raras), etiqueta)


def codificar_ordinal(serie, orden):
    """Códigos 0..n-1 según `orden`; falla si aparece una categoría no declarada."""
    desconocidas = set(serie.dropna().astype(str)) - set(orden)
    if desconocidas:
        raise ValueError(f"Categorías sin orden declarado: {sorted(desconocidas)}")
    return serie.astype(str).map({c: i for i, c in enumerate(orden)}).astype("Int64")


def codificar_orientacion(serie, plano="PLANO"):
    """Seno y coseno del ángulo de orientación; las laderas planas quedan en (0, 0)."""
    desconocidas = set(serie.dropna()) - set(ANGULOS) - {plano}
    if desconocidas:
        raise ValueError(f"Orientaciones desconocidas: {sorted(desconocidas)}")
    radianes = np.deg2rad(serie.map(ANGULOS).astype(float))
    return pd.DataFrame({"ORIENTA_SIN": np.sin(radianes).fillna(0).round(10),
                         "ORIENTA_COS": np.cos(radianes).fillna(0).round(10)}, index=serie.index)
