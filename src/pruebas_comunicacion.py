"""Pruebas de src/comunicacion.py: casos normales, límite, excepciones y cifras de control.

Mismo formato que src/pruebas_concentracion.py (utilidades.ejecutar_pruebas). Desde la raíz:

    python src/pruebas_comunicacion.py

Requiere haber ejecutado F2 y F3 (lee sus artefactos de data/processed/).
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.figure import Figure     # sin pyplot: no abre ventanas ni cambia el backend

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import comunicacion as com
import utilidades as utl

prueba, espera_error = utl.prueba, utl.espera_error


def _artefactos():
    return com.cargar_artefactos(utl.localizar_raiz() / "data" / "processed")


def _juguete():
    """Cinco glaciares de dos tipos: A = 1 + 2 + 3 = 6 km², B = 10 + 30 = 40 km²."""
    return pd.DataFrame({"TIPO": ["A", "A", "A", "B", "B"], "ZONA": ["N", "N", "S", "S", "S"],
                         "AREA_KM2": [1.0, 2.0, 3.0, 10.0, 30.0]})


def pruebas():
    a = _artefactos()
    limpio, modelo = a["limpio"], a["modelo"]
    juguete = _juguete()
    return [
        # ------------------------------------------------------------------ casos normales
        ("normal", "El contrato con F3 se cumple en todos los controles",
         lambda: prueba(com.verificar_contrato(a)["ok"].all())),
        ("normal", "composicion: % de glaciares y % de superficie suman 100",
         lambda: prueba((lambda t: np.isclose(t["pct_glaciares"].sum(), 100) and np.isclose(t["pct_magnitud"].sum(), 100))(
             com.composicion(juguete, "TIPO")))),
        ("normal", "composicion: B (2 glaciares, 40 de 46 km²) va primero con 86,96 %",
         lambda: prueba((lambda t: t.index[0] == "B" and round(t.loc["B", "pct_magnitud"], 2) == 86.96
                         and np.isclose(t["pct_acumulado"].iloc[-1], 100))(com.composicion(juguete, "TIPO")))),
        ("normal", "participacion_cruzada: cada fila suma 100",
         lambda: prueba(np.allclose(com.participacion_cruzada(juguete, "ZONA", "TIPO").sum(axis=1), 100))),
        ("normal", "Las tres implementaciones de participación por grupo coinciden",
         lambda: prueba((lambda g, v: all(np.allclose(com.participacion_por_grupo_bucle(g, v), f(g, v))
                                          for f in (com.participacion_por_grupo_pandas,
                                                    com.participacion_por_grupo_bincount)))(
             juguete["TIPO"].to_numpy(), juguete["AREA_KM2"].to_numpy()))),
        ("normal", "revertir_robusto es la inversa exacta del escalamiento",
         lambda: prueba(np.allclose(com.revertir_robusto((np.array([1.0, 3.0, 5.0]) - 3) / 2, 3, 2), [1, 3, 5]))),
        ("normal", "Formato castellano: pct, miles y decimal",
         lambda: prueba(com.pct(71.525) == "71,5 %" and com.miles(26180) == "26.180" and com.decimal(0.93731) == "0,937")),
        # ------------------------------------------------------------------- casos límite
        ("límite", "composicion con un solo grupo: 100 % y razón 1",
         lambda: prueba((lambda t: len(t) == 1 and np.isclose(t["pct_magnitud"].iloc[0], 100)
                         and np.isclose(t["razon"].iloc[0], 1))(com.composicion(juguete.assign(TIPO="A"), "TIPO")))),
        ("límite", "participacion_cruzada deja en 0 las combinaciones inexistentes",
         lambda: prueba(com.participacion_cruzada(juguete, "ZONA", "TIPO").loc["N", "B"] == 0)),
        ("límite", "gini_por_grupo con valores iguales dentro del grupo = 0",
         lambda: prueba(np.isclose(com.gini_por_grupo(pd.DataFrame({"G": ["x"] * 3, "AREA_KM2": [2.0] * 3}), "G")
                                   .loc["x", "gini"], 0))),
        ("límite", "Las funciones no modifican el DataFrame recibido",
         lambda: prueba((com.composicion(juguete, "TIPO"), com.participacion_cruzada(juguete, "ZONA", "TIPO"),
                         juguete.equals(_juguete()))[-1])),
        ("límite", "guardar_figura crea la carpeta si no existe",
         lambda: prueba(com.guardar_figura(Figure(), Path(tempfile.mkdtemp()) / "nueva", "x").is_file())),
        # --------------------------------------------------------------------- excepciones
        ("excepción", "Carpeta sin artefactos → FileNotFoundError",
         lambda: espera_error(FileNotFoundError, com.cargar_artefactos, Path(tempfile.mkdtemp()))),
        ("excepción", "Columna inexistente → KeyError",
         lambda: espera_error(KeyError, com.composicion, juguete, "COMUNA")),
        ("excepción", "composicion sin filas → ValueError",
         lambda: espera_error(ValueError, com.composicion, juguete.iloc[:0], "TIPO")),
        ("excepción", "One-hot con dos categorías activas → ValueError",
         lambda: espera_error(ValueError, com.reconstruir_categoria,
                              pd.DataFrame({"OH_TIPO_A": [1, 1], "OH_TIPO_B": [0, 1]}), "OH_TIPO_")),
        ("excepción", "Prefijo one-hot inexistente → KeyError",
         lambda: espera_error(KeyError, com.reconstruir_categoria, modelo, "OH_NO_EXISTE_")),
        ("excepción", "Escala robusta con IQR = 0 → ValueError",
         lambda: espera_error(ValueError, com.parametros_robustos, [5.0, 5.0, 5.0])),
        # ------------------------------------------------- cifras de control (inventario)
        ("control", "La copia interpretable desde glaciares_modelo coincide con glaciares_limpio",
         lambda: prueba((lambda c: (c["CLASIFICA"].to_numpy() == limpio["CLASIFICA"].astype(str).to_numpy()).all()
                         and (c["REGION"].to_numpy() == limpio["REGION"].astype(str).to_numpy()).all()
                         and np.allclose(c["AREA_KM2"], limpio["AREA_KM2"], rtol=1e-9, atol=1e-8))(
             com.copia_interpretable(modelo, limpio["LOG_AREA"])))),
        ("control", "Efluentes: 217 glaciares (0,8 %) y 65,4 % de la superficie",
         lambda: prueba((lambda f: f["glaciares"] == 217 and round(f["pct_glaciares"], 1) == 0.8
                         and round(f["pct_magnitud"], 1) == 65.4)(com.composicion(limpio, "CLASIFICA").loc["GLACIAR EFLUENTE"]))),
        ("control", "Glaciaretes: 18.211 glaciares (69,6 %) y 3,8 % de la superficie",
         lambda: prueba((lambda f: f["glaciares"] == 18211 and round(f["pct_glaciares"], 1) == 69.6
                         and round(f["pct_magnitud"], 1) == 3.8)(com.composicion(limpio, "CLASIFICA").loc["GLACIARETE"]))),
        ("control", "Gini dentro de cada clasificación entre 0,50 y 0,71",
         lambda: prueba((lambda g: round(g.min(), 2) == 0.50 and round(g.max(), 2) == 0.71)(
             com.gini_por_grupo(limpio, "CLASIFICA")["gini"]))),
        ("control", "Los efluentes solo existen en la macrozona austral (73,5 % de su superficie)",
         lambda: prueba((lambda t: round(t.loc["MACROZONA AUSTRAL", "GLACIAR EFLUENTE"], 1) == 73.5
                         and (t.drop(index="MACROZONA AUSTRAL")["GLACIAR EFLUENTE"] == 0).all())(
             com.participacion_cruzada(limpio, "MZON_GLAC", "CLASIFICA")))),
    ]


if __name__ == "__main__":
    resultado = utl.ejecutar_pruebas(pruebas())
    with pd.option_context("display.width", 160, "display.max_colwidth", 100):
        print(resultado.to_string(index=False))
    print("\n", resultado["tipo"].value_counts().to_dict())
    if not resultado["resultado"].eq("OK").all():
        sys.exit("FALLA: hay pruebas de comunicación fallidas")
    print(f"OK: {len(resultado)}/{len(resultado)} pruebas de comunicación.")
