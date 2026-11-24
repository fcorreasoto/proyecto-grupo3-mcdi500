"""Pruebas de src/figuras.py: contrato de la clase base, cada figura y cifras de sus títulos.

Mismo formato que src/pruebas_concentracion.py (utilidades.ejecutar_pruebas). Desde la raíz:

    python src/pruebas_figuras.py

Los títulos se comprueban contra las cifras de F3: si alguien cambia una tabla o un título,
la prueba falla antes de que el informe y la figura se contradigan.
"""

import sys
from pathlib import Path

if __name__ == "__main__":                      # en terminal no se abre ninguna ventana
    import matplotlib
    matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import comunicacion as com
import figuras as fg
import utilidades as utl

prueba, espera_error = utl.prueba, utl.espera_error
CLAVES_REGISTRO = {"figura", "rol", "objetivo", "grafico", "hallazgo", "evidencia"}


def _artefactos():
    return com.cargar_artefactos(utl.localizar_raiz() / "data" / "processed")


def _construye(figura):
    """True si construir() devuelve una figura con ejes y la deja disponible en .figura."""
    resultado = figura.construir()
    ok = isinstance(resultado, Figure) and len(resultado.axes) >= 1 and figura.figura is resultado
    plt.close(resultado)
    return ok


def _pruebas_base(a):
    limpio = a["limpio"]
    return [
        ("excepción", "La clase base no dibuja → NotImplementedError",
         lambda: espera_error(NotImplementedError, fg.FiguraHallazgo().construir)),
        ("excepción", "Pedir la figura antes de construirla → RuntimeError",
         lambda: espera_error(RuntimeError, lambda: fg.FiguraComposicion(limpio).figura)),
        ("límite", "tabla devuelve una copia: modificarla no altera la figura",
         lambda: prueba((lambda f: (f.tabla.iloc[:0], len(f.tabla) == 5)[1])(fg.FiguraComposicion(limpio)))),
        ("normal", "Formato de ejes en km²: 0,01 · 1 · 1.000",
         lambda: prueba([fg.etiqueta_km2(v) for v in (0.01, 1, 1000)] == ["0,01", "1", "1.000"])),
    ]


def _pruebas_principales(a):
    limpio, magnitudes, lorenz = a["limpio"], a["magnitudes"], a["lorenz"]
    principales = [fg.FiguraLorenz(lorenz, magnitudes), fg.FiguraComposicion(limpio),
                   fg.FiguraTamanoPorTipo(limpio, magnitudes)]
    return [
        ("normal", "Las figuras principales se construyen con la misma llamada (polimorfismo)",
         lambda: prueba(all(_construye(f) for f in principales))),
        ("normal", "registro() entrega las seis claves de hallazgos_f4.csv",
         lambda: prueba(all(set(f.registro()) == CLAVES_REGISTRO for f in principales))),
        ("normal", "Nombres de archivo únicos",
         lambda: prueba(len({f.nombre for f in principales}) == len(principales))),
        ("límite", "La figura de tamaño por tipo funciona con menos glaciares que la muestra (100)",
         lambda: prueba(_construye(fg.FiguraTamanoPorTipo(limpio.head(100).copy(), magnitudes)))),
        ("excepción", "Composición sin la columna CLASIFICA → KeyError",
         lambda: espera_error(KeyError, fg.FiguraComposicion, limpio.drop(columns="CLASIFICA"))),
        ("control", "Título fig. 1: el 1 % (261) reúne el 71,5 %",
         lambda: prueba(principales[0].titulo() ==
                        "El 1 % de los glaciares (261) reúne el 71,5 % de la superficie glaciar de Chile")),
        ("control", "Título fig. 2: 217 efluentes, 0,8 % del total, 65,4 % de la superficie",
         lambda: prueba(principales[1].titulo() ==
                        "217 glaciares efluentes, el 0,8 % del total, reúnen el 65,4 % de la superficie")),
        ("control", "Título fig. 3: Gini 0,50–0,71 dentro de cada tipo y 0,937 en total",
         lambda: prueba("0,50–0,71" in principales[2].titulo() and "0,937" in principales[2].titulo())),
    ]

#  figuras complementarias
def _pruebas_complementarias(a):
    limpio, magnitudes = a["limpio"], a["magnitudes"]
    complementarias = [fg.FiguraRegiones(limpio), fg.FiguraVolumenDerivado(limpio, magnitudes),
                       fg.FiguraTipoPorMacrozona(limpio)]
    return [
        ("normal", "Las figuras complementarias se construyen con la misma llamada",
         lambda: prueba(all(_construye(f) for f in complementarias))),
        ("normal", "Las complementarias se registran con rol 'complementaria'",
         lambda: prueba(all(f.registro()["rol"] == "complementaria" for f in complementarias))),
        ("límite", "Las regiones de nombre largo se abrevian; las demás conservan su nombre",
         lambda: prueba(fg.nombre_region("AYSEN DEL GENERAL CARLOS IBAÑEZ DEL CAMPO") == "Aysén"
                        and fg.nombre_region("ATACAMA") == "Atacama")),
        ("control", "Título fig. 4: Magallanes y Aysén reúnen el 91,1 %",
         lambda: prueba(complementarias[0].titulo() ==
                        "Magallanes y Aysén reúnen el 91,1 % de la superficie glaciar del país")),
        ("control", "Título fig. 5: correlación 0,999 y Gini del volumen 0,991",
         lambda: prueba("0,999" in complementarias[1].titulo() and "0,991" in complementarias[1].titulo())),
        ("control", "Título fig. 6: los efluentes reúnen el 73,5 % de la macrozona austral",
         lambda: prueba("73,5 %" in complementarias[2].titulo())),
    ]

def pruebas():
    a = _artefactos()
    return _pruebas_base(a) + _pruebas_principales(a) + _pruebas_complementarias(a)


if __name__ == "__main__":
    fg.aplicar_estilo()
    resultado = utl.ejecutar_pruebas(pruebas())
    with pd.option_context("display.width", 160, "display.max_colwidth", 100):
        print(resultado.to_string(index=False))
    print("\n", resultado["tipo"].value_counts().to_dict())
    if not resultado["resultado"].eq("OK").all():
        sys.exit("FALLA: hay pruebas de figuras fallidas")
    print(f"OK: {len(resultado)}/{len(resultado)} pruebas de figuras.")
