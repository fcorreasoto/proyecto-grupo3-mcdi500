"""Comunicación de resultados (Fase 4): de los artefactos de F3 a las tablas que se grafican.

La Fase 4 NO vuelve a limpiar ni a transformar. Este módulo:

1. Carga los artefactos que dejaron F2 y F3 en data/processed/ y se detiene con un mensaje claro
   si falta alguno (`cargar_artefactos`): no genera datos de reemplazo.
2. Verifica el contrato con F3 (`verificar_contrato`): recalcula las tablas de concentración con
   src/concentracion.py y comprueba que coinciden con las que F3 exportó.
3. Demuestra que la matriz de modelo (escalada y one-hot) y la copia interpretable
   (glaciares_limpio, en km² y con categorías legibles) son dos versiones del mismo dato
   (`copia_interpretable`). La verificación independiente se hace contra data/raw en el notebook.
4. Construye las tablas que alimentan cada figura (`composicion`, `participacion_cruzada`,
   `gini_por_grupo`) y da formato castellano a las cifras (`pct`, `miles`, `decimal`).

Las figuras viven en src/figuras.py: este módulo prepara datos y no dibuja (alta cohesión).
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd

import concentracion as con
import utilidades as utl

# Artefactos que F4 necesita: nombre lógico → archivo en data/processed/
ARTEFACTOS_F3 = {
    "limpio": "glaciares_limpio.csv",                        # F2: copia interpretable (km², categorías)
    "modelo": "glaciares_modelo.csv",                        # F2: matriz escalada y one-hot
    "magnitudes": "concentracion_magnitudes_f3.csv",         # F3: superficie, volumen y volumen desde el área
    "region": "concentracion_region_f3.csv",                 # F3: % y Gini por región
    "clasificacion": "concentracion_clasificacion_f3.csv",   # F3: % y Gini por clasificación
    "macrozona": "concentracion_macrozona_f3.csv",           # F3: % y Gini por macrozona
    "lorenz": "lorenz_f3.csv",                               # F3: curvas de Lorenz (201 puntos)
}
PREFIJO_TIPO = "OH_TIPO_"            # columnas one-hot de CLASIFICA en glaciares_modelo
PREFIJO_REGION = "OH_REG_"           # columnas one-hot de REGION en glaciares_modelo
TOLERANCIA = 1e-9


# ===================================================================== carga y contrato
def cargar_artefactos(carpeta):
    """Lee los artefactos de F2 y F3 desde `carpeta` (data/processed).

    `glaciares_limpio` se lee con `utl.cargar_limpio`, que restaura el orden de las ordinales y los
    códigos como texto; `glaciares_modelo` conserva COD_GLA como texto para poder cruzarlo.

    Lanza
    -----
    FileNotFoundError
        Si falta cualquiera de los archivos, con la lista de faltantes y qué notebook ejecutar.
    """
    carpeta = Path(carpeta)
    faltantes = [archivo for archivo in ARTEFACTOS_F3.values() if not (carpeta / archivo).is_file()]
    if faltantes:
        raise FileNotFoundError(
            f"Faltan artefactos en {carpeta}: {faltantes}. "
            "Ejecuten antes F2/F2_Procesamiento.ipynb y F3/F3_NucleoAlgoritmico.ipynb, en ese orden."
        )
    artefactos = {}
    for nombre, archivo in ARTEFACTOS_F3.items():
        ruta = carpeta / archivo
        if nombre == "limpio":
            artefactos[nombre] = utl.cargar_limpio(ruta)
        elif nombre == "modelo":
            artefactos[nombre] = pd.read_csv(ruta, dtype={"COD_GLA": "string"})
        else:
            artefactos[nombre] = pd.read_csv(ruta)
    return artefactos


def _mismas_cifras(esperada, obtenida, columnas):
    """True si dos tablas tienen las mismas filas y las mismas cifras en `columnas`."""
    if len(esperada) != len(obtenida):
        return False
    return all(np.allclose(esperada[c].to_numpy(float), obtenida[c].to_numpy(float), atol=TOLERANCIA)
               for c in columnas)


def verificar_contrato(artefactos):
    """Comprueba que lo que F3 exportó es lo que su propio código produce sobre glaciares_limpio.

    Recalcula con src/concentracion.py (las mismas clases de F3) y compara cifra a cifra. Devuelve
    una tabla `control | ok | detalle`; no lanza error, para que el notebook muestre todo el
    resultado antes de detenerse con un assert.
    """
    limpio, modelo = artefactos["limpio"], artefactos["modelo"]
    medidas = con.medidas_proyecto()
    superficie = con.AnalisisConcentracion(limpio, "AREA_KM2", medidas)
    volumen = con.AnalisisConcentracion(limpio, "VOL_km3", medidas)
    filas = []

    def registrar(control, ok, detalle=""):
        filas.append({"control": control, "ok": bool(ok), "detalle": detalle})

    registrar("limpio y modelo tienen las mismas filas y el mismo orden de COD_GLA",
              len(limpio) == len(modelo) and (limpio["COD_GLA"].to_numpy() == modelo["COD_GLA"].to_numpy()).all(),
              f"{len(limpio):,} glaciares".replace(",", "."))
    registrar("Sin nulos en las variables que se grafican",
              limpio[["AREA_KM2", "VOL_km3", "CLASIFICA", "REGION", "MZON_GLAC"]].notna().all().all())
    registrar("Superficie sin valores negativos ni nulos", (limpio["AREA_KM2"] > 0).all())

    magnitudes = con.comparar_magnitudes(limpio, medidas)
    registrar("concentracion_magnitudes_f3 = recálculo con concentracion.py",
              _mismas_cifras(artefactos["magnitudes"], magnitudes,
                             ["glaciares", "total", "pct_1%_mayores", "pct_10%_mayores", "gini"]))

    for nombre, grupo in [("region", "REGION"), ("clasificacion", "CLASIFICA"), ("macrozona", "MZON_GLAC")]:
        s = superficie.por_grupo(grupo)
        v = volumen.por_grupo(grupo).loc[s.index]
        recalculo = pd.DataFrame({"glaciares": s["glaciares"], "pct_superficie": s["pct"],
                                  "gini_superficie": s["gini"], "pct_volumen": v["pct"],
                                  "gini_volumen": v["gini"]}).reset_index()
        exportada = artefactos[nombre]
        mismo_orden = list(exportada[grupo].astype(str)) == list(recalculo[grupo].astype(str))
        registrar(f"concentracion_{nombre}_f3 = recálculo por {grupo}",
                  mismo_orden and _mismas_cifras(exportada, recalculo, list(recalculo.columns[1:])),
                  f"{len(exportada)} grupos")

    curva = superficie.curva()
    registrar("lorenz_f3 = curva de Lorenz recalculada",
              _mismas_cifras(artefactos["lorenz"].rename(columns={"prop_superficie": "prop_magnitud"}),
                             curva, ["prop_glaciares", "prop_magnitud"]),
              f"{len(curva)} puntos")
    return pd.DataFrame(filas, columns=["control", "ok", "detalle"])


# ======================================================= dos versiones del mismo dato
def parametros_robustos(serie):
    """Mediana e IQR de `serie`: los parámetros que RobustScaler aprendió en F2 (cuartiles 25–75)."""
    serie = pd.Series(serie, dtype=float)
    if serie.isna().any():
        raise ValueError("La serie de referencia tiene nulos: no se pueden estimar los parámetros")
    iqr = serie.quantile(0.75) - serie.quantile(0.25)
    if iqr == 0:
        raise ValueError("IQR = 0: la escala robusta no es invertible")
    return {"mediana": float(serie.median()), "iqr": float(iqr)}


def revertir_robusto(escalada, mediana, iqr):
    """Inversa exacta de RobustScaler: x = z · IQR + mediana."""
    return pd.Series(escalada, dtype=float) * iqr + mediana


def reconstruir_categoria(matriz, prefijo):
    """Vuelve a juntar las columnas 0/1 que empiezan con `prefijo` en una sola columna de texto.

    Lanza
    -----
    KeyError
        Si no hay columnas con ese prefijo.
    ValueError
        Si alguna fila no tiene exactamente una categoría activa (one-hot inconsistente).
    """
    columnas = [c for c in matriz.columns if c.startswith(prefijo)]
    if not columnas:
        raise KeyError(f"No hay columnas con el prefijo {prefijo!r}")
    bloque = matriz[columnas]
    activas = bloque.sum(axis=1)
    if not (activas == 1).all():
        raise ValueError(f"{prefijo}: {(activas != 1).sum()} filas sin exactamente una categoría activa")
    return bloque.idxmax(axis=1).str[len(prefijo):]


def copia_interpretable(modelo, referencia_log_area):
    """Reconstruye, desde la matriz de modelo, las variables que se grafican en unidades legibles.

    - AREA_KM2: revierte RobustScaler (parámetros de `referencia_log_area`, la LOG_AREA de
      glaciares_limpio) y luego el log10.
    - CLASIFICA y REGION: desde sus columnas one-hot.

    Sirve para demostrar que la matriz de modelo y glaciares_limpio son el mismo dato en dos
    formas: la primera para analizar y la segunda para comunicar.
    """
    p = parametros_robustos(referencia_log_area)
    return pd.DataFrame({
        "COD_GLA": modelo["COD_GLA"].to_numpy(),
        "CLASIFICA": reconstruir_categoria(modelo, PREFIJO_TIPO).to_numpy(),
        "REGION": reconstruir_categoria(modelo, PREFIJO_REGION).to_numpy(),
        "AREA_KM2": (10 ** revertir_robusto(modelo["LOG_AREA_ESC"], p["mediana"], p["iqr"])).to_numpy(),
    })


# ===================================================================== tablas para graficar
def _validar_columnas(df, columnas):
    faltan = [c for c in columnas if c not in df.columns]
    if faltan:
        raise KeyError(f"Columnas inexistentes: {faltan}")


def composicion(df, grupo, magnitud="AREA_KM2"):
    """% de glaciares y % de la magnitud que aporta cada grupo, de mayor a menor aporte.

    `razon` = % de magnitud / % de glaciares: > 1 si el grupo pesa más en superficie que en número.
    """
    _validar_columnas(df, [grupo, magnitud])
    if len(df) == 0:
        raise ValueError("No hay glaciares para calcular la composición")
    tabla = df.groupby(grupo, observed=True)[magnitud].agg(glaciares="size", total="sum")
    tabla["pct_glaciares"] = 100 * tabla["glaciares"] / tabla["glaciares"].sum()
    tabla["pct_magnitud"] = 100 * tabla["total"] / tabla["total"].sum()
    tabla["razon"] = tabla["pct_magnitud"] / tabla["pct_glaciares"]
    tabla = tabla.sort_values("pct_magnitud", ascending=False)
    tabla["pct_acumulado"] = tabla["pct_magnitud"].cumsum()
    tabla.index = tabla.index.astype(str)
    return tabla


def participacion_cruzada(df, fila, columna, magnitud="AREA_KM2"):
    """% de la magnitud de cada `fila` que aporta cada `columna` (cada fila suma 100).

    Ejemplo: fila = MZON_GLAC, columna = CLASIFICA responde «¿qué tipo de glaciar domina la
    superficie de cada macrozona?». Las combinaciones inexistentes quedan en 0.
    """
    _validar_columnas(df, [fila, columna, magnitud])
    tabla = pd.crosstab(df[fila], df[columna], values=df[magnitud], aggfunc="sum").fillna(0.0)
    return 100 * tabla.div(tabla.sum(axis=1), axis=0)


def gini_por_grupo(df, grupo, magnitud="AREA_KM2"):
    """Gini de la magnitud dentro de cada grupo, con el número de glaciares."""
    _validar_columnas(df, [grupo, magnitud])
    gini = con.IndiceGini()
    tabla = df.groupby(grupo, observed=True)[magnitud].agg(
        glaciares="size", gini=lambda v: gini.calcular(v.to_numpy()))
    tabla.index = tabla.index.astype(str)
    return tabla


def participacion_por_grupo_bucle(grupos, valores):
    """% del total por grupo recorriendo fila a fila en Python. O(n) en el intérprete.

    Implementación de referencia para la sección de eficiencia; no se usa para graficar.
    """
    totales = {}
    for g, v in zip(grupos, valores):
        totales[g] = totales.get(g, 0.0) + float(v)
    suma = sum(totales.values())
    return pd.Series({g: 100 * t / suma for g, t in totales.items()}).sort_index()


def participacion_por_grupo_pandas(grupos, valores):
    """% del total por grupo con groupby de pandas (la usada por `composicion`). O(n) vectorizado."""
    serie = pd.Series(np.asarray(valores, dtype=float)).groupby(np.asarray(grupos)).sum()
    return (100 * serie / serie.sum()).sort_index()


def participacion_por_grupo_bincount(grupos, valores):
    """% del total por grupo con np.unique + np.bincount sobre códigos enteros. O(n log n) por unique."""
    etiquetas, codigos = np.unique(np.asarray(grupos), return_inverse=True)
    sumas = np.bincount(codigos, weights=np.asarray(valores, dtype=float))
    return pd.Series(100 * sumas / sumas.sum(), index=etiquetas).sort_index()


# ===================================================================== formato y persistencia
def pct(valor, decimales=1):
    """Porcentaje (ya en escala 0–100) con coma decimal: 71.52 → '71,5 %'."""
    return f"{valor:.{decimales}f} %".replace(".", ",")


def miles(numero):
    """Entero con punto de miles: 26180 → '26.180'."""
    return f"{int(round(numero)):,}".replace(",", ".")


def decimal(valor, decimales=3):
    """Decimal con coma: 0.9373 → '0,937'."""
    return f"{valor:.{decimales}f}".replace(".", ",")


def guardar_figura(figura, carpeta, nombre, dpi=200):
    """Guarda la figura en PNG a `dpi` (200 = calidad de impresión) y devuelve la ruta."""
    os.makedirs(carpeta, exist_ok=True)
    ruta = Path(carpeta) / f"{nombre}.png"
    figura.savefig(ruta, dpi=dpi, bbox_inches="tight", facecolor="white")
    return ruta
