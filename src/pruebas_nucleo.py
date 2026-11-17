"""Pruebas del núcleo POO: transformadores, estrategias de imputación y pipeline.

Cada prueba es (tipo, descripción, función) en el formato de `utilidades.ejecutar_pruebas`, el
mismo que usan F1 y F2. El notebook de F3 las ejecuta y muestra la tabla; desde la raíz también:

    python src/pruebas_nucleo.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import imputacion as imp
import procesamiento as proc
import transformadores as tr
import utilidades as utl
from pipeline import Pipeline, RegistroEjecucion

prueba, espera_error = utl.prueba, utl.espera_error


def mini_inventario():
    """Cuatro glaciares: un HMIN = 0 en tierra, otro en fiordo, dos volúmenes 0 y un CH_CASQ."""
    return pd.DataFrame({
        "COD_GLA": ["A", "B", "C", "D"], "OBJECTID": [1, 1, 2, 3], "WGI_1": ["G", "R", "G", "V"],
        "CH_CASQ": [None, None, None, "CAMPO NORTE"], "VACIA": [None] * 4,
        "CLASIFICA": ["GLACIARETE", "GLACIAR ROCOSO", "GLACIARETE", "GLACIAR DE VALLE"],
        "FRENTE_TER": ["TIERRA", "TIERRA", "FIORDO", "LAGO"], "COMUNA": ["X", "X", "Y", "Y"],
        "AREA_KM2": [0.001, 0.5, 0.002, 10.0], "ESP_MED": [3.0, 20.0, 4.0, 100.0],
        "VOL_km3": [0.0, 0.006, 0.0, 1.0], "EQ_AGUAKM3": [0.0, 0.0055, 0.0, 0.85],
        "HMIN": [0.0, 1000.0, 0.0, 500.0], "HMEDIA": [900.0, 1100.0, 1300.0, 800.0],
        "HMAX": [1000.0, 1200.0, 1400.0, 1500.0],
    })


class _Recorta(tr.Transformador):
    """Transformador defectuoso a propósito: pierde filas."""
    def aprender(self, df):
        return {}

    def aplicar(self, df):
        return df.head(1)


def _con_nulos():
    return pd.DataFrame({"H": [1.0, np.nan, 3.0, np.nan], "G": ["a", "a", "b", "c"], "R": [5.0, 6.0, 7.0, 8.0]})


def pruebas():
    mini = mini_inventario
    return [
        # ------------------------------------------------------------------ casos normales
        ("normal", "DescartadorColumnas quita vacías, WGI_1 y OBJECTID y crea EN_CAMPO_HIELO",
         lambda: prueba((lambda r: {"VACIA", "WGI_1", "OBJECTID", "CH_CASQ"}.isdisjoint(r.columns)
                         and r["EN_CAMPO_HIELO"].tolist() == [0, 0, 0, 1])(tr.DescartadorColumnas().ajustar_transformar(mini())))),
        ("normal", "NormalizadorTexto repara 'FOTOGRAMETR├ìA' y cuenta los cambios",
         lambda: prueba((lambda t: t.ajustar_transformar(pd.DataFrame({"F": ["FOTOGRAMETR├ìA", "lidar  andina"]}))["F"].tolist()
                         == ["FOTOGRAMETRÍA", "LIDAR ANDINA"] and t.evidencia["valores_corregidos"] == 2)(tr.NormalizadorTexto()))),
        ("normal", "ReconstructorVolumen aplica AREA·ESP/1000 y marca la bandera",
         lambda: prueba((lambda r: np.isclose(r.loc[0, "VOL_km3"], 0.001 * 3 / 1000)
                         and r["VOL_RECALCULADO"].tolist() == [1, 0, 1, 0])(tr.ReconstructorVolumen().ajustar_transformar(mini())))),
        ("normal", "MarcadorFaltantes respeta el cero en fiordo y marca el de tierra",
         lambda: prueba((lambda r: r["HMIN"].isna().tolist() == [True, False, False, False])(
             tr.MarcadorFaltantes().ajustar_transformar(mini())))),
        ("normal", "Strategy: el imputador elige la estrategia sin violaciones y respeta HMIN ≤ HMEDIA",
         lambda: prueba((lambda i: (lambda r: r["HMIN_IMPUTADO"].sum() == 1 and (r["HMIN"] <= r["HMEDIA"]).all()
                                    and i.parametros["metodo"] == "HMEDIA − desnivel mediano por comuna")(
             i.ajustar_transformar(tr.MarcadorFaltantes().ajustar_transformar(mini()))))(
             tr.ImputadorEstrategia("HMIN", imp.estrategias_hmin(), limite_superior="HMEDIA")))),
        ("normal", "Strategy: cambiar la estrategia no modifica la clase que imputa",
         lambda: prueba(tr.ImputadorEstrategia("H", imp.PorMedia()).ajustar_transformar(_con_nulos())["H"].tolist()
                        == [1.0, 2.0, 3.0, 2.0]
                        and tr.ImputadorEstrategia("H", imp.PorMedianaGrupo("G")).ajustar_transformar(_con_nulos())["H"].tolist()
                        == [1.0, 1.0, 3.0, 2.0])),
        ("normal", "Lo aprendido en ajustar se aplica a otro conjunto (sin fuga de datos)",
         # aprende mediana 2 y RIC 1 de [1, 2, 3] y los aplica a 10: (10 − 2) / 1 = 8
         lambda: prueba((lambda e: e.transformar(pd.DataFrame({"X": [10.0]}))["X_ESC"].iloc[0] == 8.0)(
             tr.EscaladorRobusto(["X"]).ajustar(pd.DataFrame({"X": [1.0, 2.0, 3.0]}))))),
        ("normal", "CodificadorOneHot no crea columnas para categorías no vistas al ajustar",
         lambda: prueba((lambda c: list(c.transformar(pd.DataFrame({"T": ["B", "Z"]})).columns) == ["T", "OH_A", "OH_B"])(
             tr.CodificadorOneHot({"T": "OH"}).ajustar(pd.DataFrame({"T": ["A", "B"]}))))),
        ("normal", "Observer: el pipeline notifica un evento por paso",
         lambda: prueba((lambda reg: (Pipeline([tr.ReconstructorVolumen(), tr.MarcadorFaltantes()]).suscribir(reg)
                                      .ajustar_transformar(mini()), len(reg) == 2)[1])(RegistroEjecucion()))),
        ("normal", "Ningún paso modifica el DataFrame de entrada",
         lambda: prueba((lambda m: (Pipeline([
             tr.DescartadorColumnas(), tr.ReconstructorVolumen(), tr.MarcadorFaltantes(),
             tr.ImputadorEstrategia("HMIN", imp.estrategias_hmin(), limite_superior="HMEDIA"),
         ]).ajustar_transformar(m), m.equals(mini()))[1])(mini()))),
        ("normal", "pipeline_limpieza arma los 8 pasos de F2 en orden",
         lambda: prueba([p.nombre for p in proc.pipeline_limpieza().pasos][-3:]
                        == ["ImputadorEstrategia(HMIN)", "ImputadorPuntoMedio(HMEDIA)", "DerivadorVariables"]
                        and len(proc.pipeline_limpieza()) == 8)),
        # --------------------------------------------------------------------- casos límite
        ("límite", "Imputar una columna sin nulos no cambia valores y la bandera queda en 0",
         lambda: prueba((lambda r: r["HMAX"].equals(mini()["HMAX"]) and r["HMAX_IMPUTADO"].sum() == 0)(
             tr.ImputadorEstrategia("HMAX", imp.PorMediana()).ajustar_transformar(mini())))),
        ("límite", "Escalar una columna constante (RIC = 0) no divide por cero",
         lambda: prueba((tr.EscaladorRobusto(["c"]).ajustar_transformar(pd.DataFrame({"c": [5.0, 5.0]}))["c_ESC"] == 0).all())),
        ("límite", "Conjunto de una sola fila atraviesa el transformador",
         lambda: prueba(len(tr.ReconstructorVolumen().ajustar_transformar(mini().iloc[[3]])) == 1)),
        ("límite", "Grupo no visto al ajustar usa la mediana global",
         lambda: prueba(imp.PorMedianaGrupo("G").ajustar(_con_nulos(), "H").estimar(
             pd.DataFrame({"G": ["nuevo"], "H": [np.nan]}), "H").iloc[0] == 2.0)),
        ("límite", "Las propiedades devuelven copias: modificarlas no altera el estado interno",
         lambda: prueba((lambda t: (t.parametros.clear(), t.parametros != {})[1])(
             tr.ReconstructorVolumen().ajustar(mini())))),
        # ----------------------------------------------------------------------- excepciones
        ("excepción", "Transformar antes de ajustar → RuntimeError",
         lambda: espera_error(RuntimeError, tr.MarcadorFaltantes().transformar, mini())),
        ("excepción", "Pipeline sin ajustar → RuntimeError",
         lambda: espera_error(RuntimeError, Pipeline([tr.MarcadorFaltantes()]).transformar, mini())),
        ("excepción", "Columna requerida ausente → KeyError",
         lambda: espera_error(KeyError, tr.MarcadorFaltantes().ajustar, mini().drop(columns=["HMIN"]))),
        ("excepción", "Entrada que no es DataFrame → TypeError",
         lambda: espera_error(TypeError, tr.MarcadorFaltantes().ajustar, [1, 2])),
        ("excepción", "Pipeline con un objeto que no es Transformador → TypeError",
         lambda: espera_error(TypeError, Pipeline, [lambda df: df])),
        ("excepción", "Clase hija sin implementar aprender() → NotImplementedError",
         lambda: espera_error(NotImplementedError, tr.Transformador().ajustar, mini())),
        ("excepción", "Paso que pierde filas → ProyectoError",
         lambda: espera_error(utl.ProyectoError, _Recorta().ajustar_transformar, mini())),
        ("excepción", "Factores de volumen que no calzan con los datos → ProyectoError",
         lambda: espera_error(utl.ProyectoError, tr.ReconstructorVolumen(factor_hielo={"GLACIAR ROCOSO": 0.9}).ajustar,
                              mini().assign(VOL_km3=[3e-6, 0.006, 8e-6, 1.0]))),
        ("excepción", "Ninguna estrategia cumple la regla → ProyectoError",
         lambda: espera_error(utl.ProyectoError, tr.ImputadorEstrategia("HMIN", [imp.PorMedia(), imp.PorMediana()], "HMEDIA").ajustar,
                              tr.MarcadorFaltantes().ajustar_transformar(mini()).assign(HMEDIA=[1.0, 1100.0, 1300.0, 800.0]))),
        ("excepción", "Estrategia sin ajustar → RuntimeError",
         lambda: espera_error(RuntimeError, imp.PorMediana().estimar, mini(), "HMIN")),
        ("excepción", "Comparar varias estrategias sin límite superior → ValueError",
         lambda: espera_error(ValueError, tr.ImputadorEstrategia, "HMIN", imp.estrategias_hmin())),
        ("excepción", "Ordinal con categoría no declarada → ValueError",
         lambda: espera_error(ValueError, tr.CodificadorOrdinal("M", ["A"], "M_ORD").ajustar, pd.DataFrame({"M": ["B"]}))),
        ("excepción", "Logaritmo de un volumen 0 → ValueError",
         lambda: espera_error(ValueError, tr.DerivadorVariables().ajustar_transformar,
                              mini().assign(MZON_GLAC="MACROZONA SUR", FUENTE_DIG="X"))),
    ]


if __name__ == "__main__":
    resultado = utl.ejecutar_pruebas(pruebas())
    with pd.option_context("display.width", 160, "display.max_colwidth", 100):
        print(resultado.to_string(index=False))
    print("\n", resultado["tipo"].value_counts().to_dict())
    if not resultado["resultado"].eq("OK").all():
        sys.exit("FALLA: hay pruebas del núcleo fallidas")
    print(f"OK: {len(resultado)}/{len(resultado)} pruebas del núcleo.")
