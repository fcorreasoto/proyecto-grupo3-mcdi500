"""Pruebas de src/concentracion.py: casos normales, límite, excepciones y cifras de control.

Mismo formato que src/pruebas_nucleo.py (utilidades.ejecutar_pruebas). Desde la raíz:

    python src/pruebas_concentracion.py

Las cifras de control se calcularon sobre data/processed/glaciares_limpio.csv; si la
implementación es correcta, deben reproducirse exactamente al redondear.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import concentracion as con
import utilidades as utl

prueba, espera_error = utl.prueba, utl.espera_error

MAGALLANES = "MAGALLANES Y ANTARTICA CHILENA"
AYSEN = "AYSEN DEL GENERAL CARLOS IBAÑEZ DEL CAMPO"


def _limpio():
    return utl.cargar_limpio(utl.localizar_raiz() / "data" / "processed" / "glaciares_limpio.csv")


def _medidas():
    return con.medidas_proyecto()


def _resumen(df, magnitud):
    return con.AnalisisConcentracion(df, magnitud, _medidas()).resumen()


def _dos_mayores(df, magnitud):
    tabla = con.AnalisisConcentracion(df, magnitud, _medidas()).por_grupo("REGION")
    return round(float(tabla.loc[[MAGALLANES, AYSEN], "pct"].sum()), 1)


def pruebas():
    df = _limpio()
    return [
        # ------------------------------------------------------------------ casos normales
        ("normal", "Participación del 50 % mayor en [1, 2, 3, 4] = 70 %",
         lambda: prueba(np.isclose(con.ParticipacionMayores(0.5).calcular([1, 2, 3, 4]), 70.0))),
        ("normal", "Gini de [1, 2, 3, 4] = 0,25",
         lambda: prueba(np.isclose(con.IndiceGini().calcular([1, 2, 3, 4]), 0.25))),
        ("normal", "Lorenz empieza en (0, 0) y termina en (1, 1)",
         lambda: prueba((lambda c: list(c.iloc[0]) == [0.0, 0.0] and np.allclose(list(c.iloc[-1]), [1.0, 1.0]))(
             con.CurvaLorenz(puntos=5).calcular([1, 2, 3, 4])))),
        ("normal", "Polimorfismo: el análisis acepta cualquier MedidaConcentracion",
         lambda: prueba(set(con.AnalisisConcentracion(pd.DataFrame({"M": [1.0, 2.0]}), "M",
                                                      [con.IndiceGini(), con.ParticipacionMayores(0.5)]).resumen())
                        >= {"gini", con.ParticipacionMayores(0.5).etiqueta})),
        ("normal", "por_grupo suma 100 % y está ordenado de mayor a menor",
         lambda: prueba((lambda t: np.isclose(t["pct"].sum(), 100) and t["pct"].is_monotonic_decreasing)(
             con.AnalisisConcentracion(df, "AREA_KM2", _medidas()).por_grupo("CLASIFICA")))),
        # ------------------------------------------------------------------- casos límite
        ("límite", "Gini de valores iguales = 0",
         lambda: prueba(np.isclose(con.IndiceGini().calcular([5, 5, 5, 5]), 0.0))),
        ("límite", "Gini con un solo glaciar con todo = (n − 1) / n",
         lambda: prueba(np.isclose(con.IndiceGini().calcular([0, 0, 0, 10]), 0.75))),
        ("límite", "Participación con fracción 1 = 100 %",
         lambda: prueba(np.isclose(con.ParticipacionMayores(1.0).calcular([3, 1, 2]), 100.0))),
        ("límite", "Un solo valor: Gini 0 y Lorenz de dos puntos",
         lambda: prueba(np.isclose(con.IndiceGini().calcular([7]), 0.0)
                        and len(con.CurvaLorenz(puntos=2).calcular([7])) == 2)),
        ("límite", "El análisis no modifica el DataFrame recibido",
         lambda: prueba((lambda m: (con.AnalisisConcentracion(m, "M", [con.IndiceGini()]).resumen(),
                                    m.equals(pd.DataFrame({"M": [3.0, 1.0, 2.0]})))[1])(pd.DataFrame({"M": [3.0, 1.0, 2.0]})))),
        # --------------------------------------------------------------------- excepciones
        ("excepción", "Valores vacíos → ValueError", lambda: espera_error(ValueError, con.IndiceGini().calcular, [])),
        ("excepción", "Valores negativos → ValueError", lambda: espera_error(ValueError, con.IndiceGini().calcular, [1, -2])),
        ("excepción", "Valores nulos → ValueError", lambda: espera_error(ValueError, con.IndiceGini().calcular, [1, np.nan])),
        ("excepción", "Fracción fuera de (0, 1] → ValueError", lambda: espera_error(ValueError, con.ParticipacionMayores, 1.5)),
        ("excepción", "Fracción que no alcanza a un glaciar → ValueError",
         lambda: espera_error(ValueError, con.ParticipacionMayores(0.01).calcular, [1, 2, 3])),
        ("excepción", "Magnitud inexistente → KeyError",
         lambda: espera_error(KeyError, con.AnalisisConcentracion, df, "NO_EXISTE", _medidas())),
        ("excepción", "Medida que no es MedidaConcentracion → TypeError",
         lambda: espera_error(TypeError, con.AnalisisConcentracion, df, "AREA_KM2", [np.sum])),
        ("excepción", "Valores que suman cero → ValueError", lambda: espera_error(ValueError, con.IndiceGini().calcular, [0, 0])),
        ("excepción", "Grupo inexistente → KeyError",
         lambda: espera_error(KeyError, con.AnalisisConcentracion(df, "AREA_KM2", _medidas()).por_grupo, "COMUNA")),
        ("excepción", "Clase base sin _calcular → NotImplementedError",
         lambda: espera_error(NotImplementedError, con.MedidaConcentracion().calcular, [1, 2])),
        # ------------------------------------------------- cifras de control (inventario)
        ("control", "Superficie: 1 % mayor = 71,5 %, 10 % mayor = 91,1 %, Gini = 0,937",
         lambda: prueba((lambda r: [round(r[m.etiqueta], 1) for m in _medidas()[:2]] == [71.5, 91.1]
                         and round(r["gini"], 3) == 0.937)(_resumen(df, "AREA_KM2")))),
        ("control", "Volumen: 1 % mayor = 93,8 %, 10 % mayor = 99,1 %, Gini = 0,991",
         lambda: prueba((lambda r: [round(r[m.etiqueta], 1) for m in _medidas()[:2]] == [93.8, 99.1]
                         and round(r["gini"], 3) == 0.991)(_resumen(df, "VOL_km3")))),
        ("control", "Magallanes + Aysén: 91,1 % de la superficie y 97,9 % del volumen",
         lambda: prueba(_dos_mayores(df, "AREA_KM2") == 91.1 and _dos_mayores(df, "VOL_km3") == 97.9)),
        ("control", "El volumen calculado solo desde el área reproduce la concentración del volumen",
         lambda: prueba((lambda t: t.loc["VOL_km3", "gini"].round(3) == t.loc["VOL_DESDE_AREA", "gini"].round(3)
                         and t.loc["VOL_km3", _medidas()[0].etiqueta].round(1) == t.loc["VOL_DESDE_AREA", _medidas()[0].etiqueta].round(1)
                         and t.loc["VOL_km3", "gini"] > t.loc["AREA_KM2", "gini"])(
             con.comparar_magnitudes(df, _medidas()).set_index("magnitud")))),
        # --------------------------------------- índice de Theil y su descomposición (F4)
        ("normal", "Theil de [1, 1, 2] coincide con la fórmula escrita a mano",
         lambda: prueba(np.isclose(con.IndiceTheil().calcular([1, 1, 2]),
                                   np.mean([0.75 * np.log(0.75)] * 2 + [1.5 * np.log(1.5)])))),
        ("normal", "Descomposición: entre + dentro = Theil total",
         lambda: prueba((lambda d: np.isclose(d["entre"] + d["dentro"], d["theil_total"])
                         and np.isclose(d["pct_entre"] + d["pct_dentro"], 100))(
             con.descomponer_theil(_JUGUETE, "G", "M")))),
        ("límite", "Theil de valores iguales = 0 y con un solo glaciar con todo = ln(n)",
         lambda: prueba(np.isclose(con.IndiceTheil().calcular([4, 4, 4]), 0)
                        and np.isclose(con.IndiceTheil().calcular([0, 0, 0, 9]), np.log(4)))),
        ("límite", "Un solo grupo: todo es desigualdad dentro (entre = 0)",
         lambda: prueba(np.isclose(con.descomponer_theil(_JUGUETE.assign(G="a"), "G", "M")["entre"], 0))),
        ("límite", "Un grupo por glaciar: todo es desigualdad entre (dentro = 0)",
         lambda: prueba(np.isclose(con.descomponer_theil(_JUGUETE.assign(G=list("pqrs")), "G", "M")["dentro"], 0))),
        ("excepción", "Descomposición con un grupo inexistente → KeyError",
         lambda: espera_error(KeyError, con.descomponer_theil, _JUGUETE, "COMUNA", "M")),
        ("excepción", "Theil con valores negativos → ValueError",
         lambda: espera_error(ValueError, con.IndiceTheil().calcular, [1, -1, 2])),
        ("control", "Theil de la superficie = 3,793; la clasificación da cuenta del 77,6 % y la región del 5,7 %",
         lambda: prueba(round(con.IndiceTheil().calcular(df["AREA_KM2"]), 3) == 3.793
                        and round(con.descomponer_theil(df, "CLASIFICA")["pct_entre"], 1) == 77.6
                        and round(con.descomponer_theil(df, "REGION")["pct_entre"], 1) == 5.7)),
    ]


_JUGUETE = pd.DataFrame({"G": ["a", "a", "b", "b"], "M": [1.0, 3.0, 10.0, 30.0]})


if __name__ == "__main__":
    resultado = utl.ejecutar_pruebas(pruebas())
    with pd.option_context("display.width", 160, "display.max_colwidth", 100):
        print(resultado.to_string(index=False))
    print("\n", resultado["tipo"].value_counts().to_dict())
    if not resultado["resultado"].eq("OK").all():
        sys.exit("FALLA: hay pruebas de concentración fallidas")
    print(f"OK: {len(resultado)}/{len(resultado)} pruebas de concentración.")