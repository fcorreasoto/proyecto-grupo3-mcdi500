"""Arma los pipelines de F2 con los transformadores y verifica que reproducen sus salidas.

Este módulo es el único que conoce la configuración concreta del proyecto (qué pasos, en qué
orden y con qué columnas). `transformadores.py` y `pipeline.py` no dependen de él, así que
cambiar una decisión de F2 (por ejemplo, la estrategia de imputación) solo modifica este archivo.

Flujo
-----
    CSV original ──► pipeline_limpieza() ──► transformado ──┬─► pipeline_formato() ──► limpio
                                                            └─► pipeline_modelo()  ──► modelo

Verificación de la Fase 3: `verificar_reproduccion()` regenera los tres CSV de data/processed en
una carpeta temporal y compara su SHA-256 con los versionados por F2. Desde la raíz:

    python src/procesamiento.py
"""

import sys
import tempfile
from pathlib import Path

import pandas as pd

if __package__ in (None, ""):              # permite `python src/procesamiento.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import imputacion as imp
import limpieza as lim
import transformadores as tr
import utilidades as utl
from pipeline import Pipeline

CONTINUAS = ["LOG_AREA", "HMEDIA", "RANGO_ALT", "PENDIENTE"]   # LOG_VOL y ESP_MED excluidas: dependen del área
NOMINALES = ["CLASIFICA", "REGION", "FRENTE_TER", "FUENTE_GRUPO"]
BANDERAS = ["EN_CAMPO_HIELO", "FRENTE_AGUA", "VOL_RECALCULADO", "EQ_RECALCULADO", "HMIN_IMPUTADO", "HMEDIA_IMPUTADO"]
PREFIJOS_ONE_HOT = {"CLASIFICA": "OH_TIPO", "FRENTE_TER": "OH_FRENTE", "REGION": "OH_REG", "FUENTE_GRUPO": "OH_FUENTE"}
ARCHIVOS_SALIDA = ("glaciares_limpio.csv", "glaciares_modelo.csv", "perfil_glaciares_limpio.csv")

# Decisión que justifica cada paso (misma redacción que la bitácora de F2), para ObservadorBitacora
DECISIONES = {
    "DescartadorColumnas": "Se descartan columnas sin información y redundantes; CH_CASQ pasa a EN_CAMPO_HIELO",
    "NormalizadorTexto": "Se normaliza el texto (codificación, mayúsculas y espacios)",
    "ConversorTipos": "Casting: coordenadas a float, FUEN_FECHA a fecha + FUEN_ANIO, códigos a texto",
    "ReconstructorVolumen": "Se recalculan los ceros de VOL_km3 y EQ_AGUAKM3 con la fórmula del inventario",
    "MarcadorFaltantes": "Los faltantes encubiertos de HMIN y HMEDIA se marcan como NaN",
    "ImputadorEstrategia(HMIN)": "HMIN se imputa con la estrategia elegida por la regla declarada",
    "ImputadorPuntoMedio(HMEDIA)": "HMEDIA incoherente se reemplaza por (HMIN + HMAX) / 2",
    "DerivadorVariables": "Se derivan RANGO_ALT, LOG_AREA, LOG_VOL, CLASE_TAMANO, FRENTE_AGUA y FUENTE_GRUPO",
    "CodificadorOneHot": "One-hot para CLASIFICA, FRENTE_TER, REGION y FUENTE_GRUPO",
}


# ===================================================================== construcción
def pipeline_limpieza(estrategias_hmin=None):
    """Limpieza, imputación y derivación de F2 (secciones 3 y 4).

    `estrategias_hmin` permite inyectar otras estrategias de imputación sin tocar ninguna clase.
    """
    estrategias = imp.estrategias_hmin() if estrategias_hmin is None else estrategias_hmin
    return Pipeline([
        tr.DescartadorColumnas(),
        tr.NormalizadorTexto(),
        tr.ConversorTipos(),
        tr.ReconstructorVolumen(),
        tr.MarcadorFaltantes(),
        tr.ImputadorEstrategia("HMIN", estrategias, limite_superior="HMEDIA"),
        tr.ImputadorPuntoMedio("HMEDIA", "HMIN", "HMAX"),
        tr.DerivadorVariables(),
    ], nombre="limpieza")


def pipeline_formato(decimales=12):
    """Formato de glaciares_limpio: redondeo de los logaritmos y nominales como categoría."""
    return Pipeline([tr.Redondeador(["LOG_AREA", "LOG_VOL"], decimales), tr.Categorizador(NOMINALES)],
                    nombre="formato")


def pipeline_modelo(decimales=12):
    """Matriz numérica de F2 (sección 6.1): ordinales, cíclicas, banderas, escaladas y one-hot."""
    escaladas = [f"{c}_ESC" for c in CONTINUAS]
    return Pipeline([
        tr.CodificadorOrdinal("MZON_GLAC", utl.ORDEN_MACROZONA, "MZON_ORD"),
        tr.CodificadorOrdinal("CLASE_TAMANO", utl.ETIQUETAS_TAMANO, "TAMANO_ORD"),
        tr.CodificadorCiclico("ORIENTA"),
        tr.EscaladorRobusto(CONTINUAS, decimales),
        tr.CodificadorOneHot(PREFIJOS_ONE_HOT),
    ], nombre="modelo")


def columnas_modelo(df):
    """Orden de columnas de glaciares_modelo.csv (clave, ordinales, cíclicas, banderas, escaladas, one-hot)."""
    one_hot = [c for c in df.columns if any(c.startswith(p + "_") for p in PREFIJOS_ONE_HOT.values())]
    return ["COD_GLA", "MZON_ORD", "TAMANO_ORD", "ORIENTA_SIN", "ORIENTA_COS", *BANDERAS,
            *[f"{c}_ESC" for c in CONTINUAS], *one_hot]


# ======================================================================= ejecución
def procesar(original, observadores=()):
    """Ejecuta los tres pipelines sobre el inventario original y devuelve (limpio, modelo, pipelines)."""
    pipelines = {"limpieza": pipeline_limpieza(), "formato": pipeline_formato(), "modelo": pipeline_modelo()}
    for pipeline in pipelines.values():
        for observador in observadores:
            pipeline.suscribir(observador)
    transformado = pipelines["limpieza"].ajustar_transformar(original)
    limpio = pipelines["formato"].ajustar_transformar(transformado)
    codificado = pipelines["modelo"].ajustar_transformar(transformado)
    modelo = codificado[columnas_modelo(codificado)]
    return limpio, modelo, pipelines


def cargar_original(raiz=None):
    """Verifica la huella del CSV original y lo carga sin modificarlo."""
    raiz = utl.localizar_raiz() if raiz is None else Path(raiz)
    ruta = raiz / "data" / "raw" / utl.ARCHIVO_INVENTARIO
    utl.verificar_huella(ruta)
    return utl.cargar_inventario(ruta)


def guardar_salidas(limpio, modelo, carpeta):
    """Escribe los tres CSV de data/processed con el mismo formato que F2; devuelve sus rutas."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = [carpeta / nombre for nombre in ARCHIVOS_SALIDA]
    limpio.to_csv(rutas[0], index=False, date_format="%Y-%m-%d")
    modelo.to_csv(rutas[1], index=False)
    lim.perfil_columnas(limpio).to_csv(rutas[2], index=False)
    return rutas


def comparar_con_versionados(limpio, modelo, raiz=None):
    """Guarda las salidas en una carpeta temporal y compara su SHA-256 con las de data/processed."""
    raiz = utl.localizar_raiz() if raiz is None else Path(raiz)
    filas = []
    with tempfile.TemporaryDirectory() as carpeta:
        for ruta in guardar_salidas(limpio, modelo, carpeta):
            nueva = utl.huella_sha256(ruta)
            versionada = utl.huella_sha256(raiz / "data" / "processed" / ruta.name)
            filas.append({"archivo": ruta.name, "sha256_F2": versionada[:16], "sha256_F3": nueva[:16],
                          "identico": nueva == versionada})
    return pd.DataFrame(filas)


def verificar_reproduccion(raiz=None, observadores=()):
    """Carga, procesa con las clases y compara con F2. Devuelve (tabla, limpio, modelo, pipelines)."""
    limpio, modelo, pipelines = procesar(cargar_original(raiz), observadores)
    return comparar_con_versionados(limpio, modelo, raiz), limpio, modelo, pipelines


if __name__ == "__main__":
    from pipeline import ReporteConsola
    tabla, *_ = verificar_reproduccion(observadores=[ReporteConsola()])
    print()
    print(tabla.to_string(index=False))
    if not tabla["identico"].all():
        sys.exit("FALLA: las clases no reproducen los archivos de F2 byte a byte")
    print("\nOK: las clases reproducen los tres archivos de data/processed byte a byte.")
