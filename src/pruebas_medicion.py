"""Pruebas de medicion.py y metadatos.py: casos normales, límite y excepciones.

Mismo formato que src/pruebas_nucleo.py (utilidades.ejecutar_pruebas). Desde la raíz:

    python src/pruebas_medicion.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import medicion as me
import metadatos as md
import utilidades as utl

prueba, espera_error = utl.prueba, utl.espera_error

METADATOS_EJEMPLO = {"proyecto": {"fase": "F3", "semilla": 42},
                     "decisiones": {"imputacion": {"HMIN": {"metodo": "diferencia", "valores": 33}}, "one_hot": ["A", "B"]}}


def pruebas():
    x = me.muestras(np.arange(1, 501), [300])[300]
    texto = pd.Series(["FOTOGRAMETR├ìA", "lidar  andina", None, "lidar  andina"])
    return [
        # ------------------------------------------------------------------ casos normales
        ("normal", "medir devuelve tiempo, memoria y el resultado de la función",
         lambda: prueba((lambda r: r["resultado"] == 6 and r["segundos"] >= 0 and r["memoria_mb"] >= 0)(me.medir(sum, [1, 2, 3])))),
        ("normal", "Las tres implementaciones del Gini dan el mismo valor",
         lambda: prueba(np.isclose(me.gini_pares_matriz(x), me.gini_pares_bucle(x)) and np.isclose(me.gini_pares_bucle(x), me.gini_ordenado(x)))),
        ("normal", "Las tres formas de calcular la participación dan el mismo valor",
         lambda: prueba(np.isclose(me.participacion_nlargest(x), me.participacion_orden_total(x))
                        and np.isclose(me.participacion_orden_total(x), me.participacion_particion(x)))),
        ("normal", "Normalizar por valores únicos = normalizar fila a fila (F2)",
         lambda: prueba(me.normalizar_por_valores_unicos(texto).equals(me.normalizar_fila_a_fila(texto)))),
        ("normal", "aplanar recursivo e iterativo dan el mismo diccionario y orden de claves",
         lambda: prueba(md.aplanar(METADATOS_EJEMPLO) == md.aplanar_iterativo(METADATOS_EJEMPLO)
                        and list(md.aplanar(METADATOS_EJEMPLO)) == list(md.aplanar_iterativo(METADATOS_EJEMPLO)))),
        ("normal", "comparar devuelve una fila por tamaño e implementación",
         lambda: prueba(len(me.comparar({"a": np.sum, "b": lambda v: float(np.sum(v))}, {10: np.ones(10), 20: np.ones(20)},
                                        repeticiones=1)) == 4)),
        ("normal", "exponente_empirico recupera b = 1 en un costo lineal y b = 2 en uno cuadrático",
         lambda: prueba((lambda e: e.tolist() == [1.0, 2.0])(me.exponente_empirico(pd.DataFrame({
             "n": [10, 100, 1000] * 2, "implementacion": ["lineal"] * 3 + ["cuadratica"] * 3,
             "ms": [1, 10, 100, 1, 100, 10000]}))["exponente_tiempo"]))),
        ("normal", "profundidad de los metadatos de ejemplo = 4",
         lambda: prueba(md.profundidad(METADATOS_EJEMPLO) == 4)),
        # --------------------------------------------------------------------- casos límite
        ("límite", "aplanar un diccionario vacío devuelve {} en ambas versiones",
         lambda: prueba(md.aplanar({}) == {} == md.aplanar_iterativo({}))),
        ("límite", "La versión iterativa aplana 5.000 niveles; la recursiva supera el límite de Python",
         lambda: prueba(len(md.aplanar_iterativo(md.anidar(5000))) == 5000 and _recursion_falla(md.anidar(5000)))),
        ("límite", "muestras con la misma semilla son idénticas",
         lambda: prueba(np.array_equal(me.muestras(np.arange(100), [50])[50], me.muestras(np.arange(100), [50])[50]))),
        ("límite", "Gini de un solo valor = 0 en las tres implementaciones",
         lambda: prueba(me.gini_pares_matriz([4.0]) == me.gini_pares_bucle([4.0]) == me.gini_ordenado([4.0]) == 0.0)),
        # ----------------------------------------------------------------------- excepciones
        ("excepción", "Implementaciones que no coinciden → ProyectoError",
         lambda: espera_error(utl.ProyectoError, me.comparar, {"a": np.sum, "b": np.mean}, {5: np.arange(5.0)}, 1)),
        ("excepción", "repeticiones < 1 → ValueError", lambda: espera_error(ValueError, me.medir, sum, [1], repeticiones=0)),
        ("excepción", "Exponente con un solo tamaño → ValueError",
         lambda: espera_error(ValueError, me.exponente_empirico, pd.DataFrame({"n": [10], "implementacion": ["a"], "ms": [1.0]}))),
        ("excepción", "aplanar algo que no es diccionario → TypeError (ambas versiones)",
         lambda: (espera_error(TypeError, md.aplanar, ["x"]), espera_error(TypeError, md.aplanar_iterativo, ["x"]))),
    ]


def _recursion_falla(estructura):
    """True si la versión recursiva excede el límite de recursión de Python."""
    try:
        md.aplanar(estructura)
    except RecursionError:
        return True
    return False


if __name__ == "__main__":
    resultado = utl.ejecutar_pruebas(pruebas())
    with pd.option_context("display.width", 160, "display.max_colwidth", 100):
        print(resultado.to_string(index=False))
    print("\n", resultado["tipo"].value_counts().to_dict())
    if not resultado["resultado"].eq("OK").all():
        sys.exit("FALLA: hay pruebas de medición fallidas")
    print(f"OK: {len(resultado)}/{len(resultado)} pruebas de medición y recursividad.")
