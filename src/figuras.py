"""Figuras de la Fase 4: cada figura responde un objetivo y su título dice el hallazgo.

Diseño (mismo contrato que transformadores.py y concentracion.py):

- `FiguraHallazgo` es la clase base. Su método plantilla `construir` crea la figura, delega el
  dibujo en `_dibujar` (lo implementa cada hija), pone el título-hallazgo y la fuente. Así las
  seis figuras comparten estilo, fuente y forma de guardarse sin repetir código (herencia).
- Cada clase hija calcula en `__init__` la tabla que grafica (con src/comunicacion.py) y la
  conserva: `titulo()` y `evidencia()` leen las cifras de esa misma tabla, de modo que el título
  de la figura, la tabla docs/hallazgos_f4.csv y el informe no pueden contradecirse.
- El notebook recorre la lista de figuras con las mismas llamadas (`construir`, `guardar`,
  `registro`) sin preguntar su tipo (polimorfismo).
- La figura construida y la tabla son atributos internos (`_figura`, `_tabla`) que se leen con
  propiedades (encapsulamiento); pedir la figura antes de construirla es un error explícito.

Regla de estilo: seaborn dibuja la geometría estadística (caja, mapa de calor) y Matplotlib
termina (título, anotaciones, fuente). El color tiene función: GRANATE marca el hallazgo.
"""

import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter, PercentFormatter

import comunicacion as com
import concentracion as con

# ================================================================================ estilo
GRANATE = "#AC212E"     # el dato que se quiere destacar
AZUL = "#06304A"        # dato de comparación
NEUTRO = "#9FB6C8"      # contexto
GRIS = "#8A94A0"        # lo secundario
TINTA = "#0A1526"       # texto
HIELO = "#D7E3EE"       # fondos y bandas de referencia

# Un color fijo por clasificación en todas las figuras: el lector aprende la clave una vez
COLORES_TIPO = {
    "GLACIAR EFLUENTE": GRANATE,
    "GLACIAR DE VALLE": AZUL,
    "GLACIAR DE MONTAÑA": "#3C6E91",
    "GLACIARETE": NEUTRO,
    "GLACIAR ROCOSO": "#B59B7A",
}
NOMBRES_REGION = {
    "MAGALLANES Y ANTARTICA CHILENA": "Magallanes",
    "AYSEN DEL GENERAL CARLOS IBAÑEZ DEL CAMPO": "Aysén",
    "LIBERTADOR BERNARDO O HIGGINS": "O'Higgins",
    "METROPOLITANA DE SANTIAGO": "Metropolitana",
    "ARICA Y PARINACOTA": "Arica y Parinacota",
    "DEL MAULE": "Maule",
    "ARAUCANIA": "Araucanía",
    "BIOBIO": "Biobío",
    "TARAPACA": "Tarapacá",
    "VALPARAISO": "Valparaíso",
    "LOS RIOS": "Los Ríos",
}
FUENTE = ("Fuente: elaboración propia con el Inventario Público de Glaciares de Chile 2022 (DGA), "
          "26.180 glaciares.")


def aplicar_estilo():
    """Tema común de todas las figuras. Se llama una vez, al inicio del notebook."""
    sns.set_theme(style="white")
    plt.rcParams.update({
        "figure.dpi": 110,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titlelocation": "left",
        "axes.labelsize": 10,
        "axes.labelcolor": TINTA,
        "axes.edgecolor": GRIS,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": TINTA,
        "ytick.color": TINTA,
        "legend.frameon": False,
    })


def nombre_tipo(clasificacion):
    """'GLACIAR DE MONTAÑA' → 'Glaciar de montaña'."""
    return str(clasificacion).capitalize()


def nombre_region(region):
    return NOMBRES_REGION.get(str(region), str(region).title())


def _formato_pct_eje(eje, escala=100):
    """Eje en porcentaje con coma decimal; `escala` = 100 si los datos ya están en %."""
    eje.set_major_formatter(PercentFormatter(escala, decimals=0))


def etiqueta_km2(valor, _=None):
    """Etiqueta de un eje logarítmico en km² con coma decimal: 0,001 · 0,1 · 10 · 1.000."""
    if valor >= 1:
        return com.miles(valor)
    return f"{valor:g}".replace(".", ",")


def formato_eje_km2(eje):
    """Aplica `etiqueta_km2` a un eje (eje.xaxis o eje.yaxis)."""
    eje.set_major_formatter(FuncFormatter(etiqueta_km2))


# ========================================================================= clase base
class FiguraHallazgo:
    """Contrato común de las figuras del informe. No se usa directamente.

    Atributos de clase que define cada hija:
      nombre    archivo de salida (sin extensión) y clave en hallazgos_f4.csv
      rol       'principal' (va al cuerpo del informe) o 'complementaria' (anexo / video)
      objetivo  objetivo específico o pregunta que responde
      grafico   tipo de gráfico, para la tabla de vinculación
      tamano    (ancho, alto) en pulgadas
    """

    nombre = "sin_nombre"
    rol = "principal"
    objetivo = ""
    grafico = ""
    tamano = (8.5, 4.8)
    ancho_titulo = 85          # caracteres por línea del título antes de partirlo

    def __init__(self, fuente=FUENTE):
        self._fuente = fuente
        self._figura = None
        self._tabla = None

    # ------------------------------------------------------------- método plantilla
    def construir(self):
        """Crea la figura, delega el dibujo y agrega título-hallazgo y fuente. Devuelve la figura."""
        figura = plt.figure(figsize=self.tamano, layout="constrained")
        self._dibujar(figura)
        figura.suptitle(textwrap.fill(self.titulo(), self.ancho_titulo), x=0.01, ha="left", fontsize=12.5, fontweight="bold", color=TINTA)
        figura.text(0.01, -0.01, self._fuente, fontsize=7.5, color=GRIS, ha="left", va="top")
        self._figura = figura
        return figura

    # ------------------------------------------------------- lo que implementa cada hija
    def _dibujar(self, figura):
        raise NotImplementedError(f"{type(self).__name__} debe implementar _dibujar()")

    def titulo(self):
        """El hallazgo, con la cifra que lo respalda (no el tema del gráfico)."""
        raise NotImplementedError(f"{type(self).__name__} debe implementar titulo()")

    def evidencia(self):
        """Las cifras exactas detrás del título, para docs/hallazgos_f4.csv."""
        raise NotImplementedError(f"{type(self).__name__} debe implementar evidencia()")

    # --------------------------------------------------------------------- comunes
    @property
    def figura(self):
        if self._figura is None:
            raise RuntimeError(f"{self.nombre}: hay que llamar a construir() antes de usar la figura")
        return self._figura

    @property
    def tabla(self):
        """Copia de la tabla graficada: quien la lea no puede alterar la figura."""
        return None if self._tabla is None else self._tabla.copy()

    def guardar(self, carpeta, dpi=200):
        return com.guardar_figura(self.figura, carpeta, self.nombre, dpi=dpi)

    def registro(self):
        return {"figura": self.nombre, "rol": self.rol, "objetivo": self.objetivo,
                "grafico": self.grafico, "hallazgo": self.titulo(), "evidencia": self.evidencia()}

    def __repr__(self):
        return f"{type(self).__name__}(nombre={self.nombre!r})"


# ======================================================= figuras principales (acto 1–3)
class FiguraLorenz(FiguraHallazgo):
    """Acto 1 · Contexto: la superficie glaciar está extremadamente concentrada."""

    nombre = "fig1_lorenz_superficie"
    objetivo = "OE3 · ¿Qué tan concentrada está la superficie glaciar en pocos glaciares?"
    grafico = "Líneas (curva de Lorenz) con detalle del 10 % mayor"
    tamano = (10, 4.8)

    def __init__(self, lorenz, magnitudes, **kwargs):
        super().__init__(**kwargs)
        self._tabla = lorenz.copy()
        fila = magnitudes.set_index("magnitud")
        self._sup = fila.loc["AREA_KM2"]
        self._vol = fila.loc["VOL_km3"]
        self._n_1 = int(self._sup["glaciares"] * 0.01)

    def titulo(self):
        return (f"El 1 % de los glaciares ({com.miles(self._n_1)}) reúne el "
                f"{com.pct(self._sup['pct_1%_mayores'])} de la superficie glaciar de Chile")

    def evidencia(self):
        return (f"1 % mayor: {com.pct(self._sup['pct_1%_mayores'])}; 10 % mayor: "
                f"{com.pct(self._sup['pct_10%_mayores'])}; Gini superficie {com.decimal(self._sup['gini'])} "
                f"(volumen derivado {com.decimal(self._vol['gini'])}) sobre "
                f"{com.miles(self._sup['total'])} km²")

    def _panel(self, eje, x_min):
        t = self._tabla
        eje.fill_between(t["prop_glaciares"], t["prop_superficie"], t["prop_glaciares"], color=HIELO, alpha=0.6, lw=0)
        eje.plot([0, 1], [0, 1], color=GRIS, lw=1, ls="--", label="Igualdad perfecta (Gini 0)")
        eje.plot(t["prop_glaciares"], t["prop_volumen"], color=AZUL, lw=1.3, ls=":",
                 label=f"Volumen, derivado del área (Gini {com.decimal(self._vol['gini'])})")
        eje.plot(t["prop_glaciares"], t["prop_superficie"], color=GRANATE, lw=2.2,
                 label=f"Superficie (Gini {com.decimal(self._sup['gini'])})")
        eje.set_xlim(x_min, 1)
        eje.set_ylim(0, 1)
        _formato_pct_eje(eje.xaxis, 1)
        _formato_pct_eje(eje.yaxis, 1)

    def _dibujar(self, figura):
        izquierda, derecha = figura.subplots(1, 2, gridspec_kw={"width_ratios": [1, 1]})
        self._panel(izquierda, 0)
        izquierda.set_title("Todos los glaciares, de menor a mayor", color=TINTA)
        izquierda.set_xlabel("Glaciares acumulados (de menor a mayor superficie)")
        izquierda.set_ylabel("Superficie acumulada")
        izquierda.axvspan(0.9, 1, color=GRANATE, alpha=0.06)
        izquierda.legend(loc="upper left", fontsize=8.5)

        self._panel(derecha, 0.9)
        derecha.set_title("Detalle: el 10 % de glaciares más grandes", color=TINTA)
        derecha.set_xlabel("Glaciares acumulados")
        y_99 = float(np.interp(0.99, self._tabla["prop_glaciares"], self._tabla["prop_superficie"]))
        y_90 = float(np.interp(0.90, self._tabla["prop_glaciares"], self._tabla["prop_superficie"]))
        for x, y, texto, lado in [(0.99, y_99, f"1 % mayor\n{com.pct(self._sup['pct_1%_mayores'])}", -1),
                                  (0.902, y_90, f"10 % mayor\n{com.pct(self._sup['pct_10%_mayores'])}", 1)]:
            derecha.annotate("", xy=(x, 1), xytext=(x, y),
                             arrowprops={"arrowstyle": "<->", "color": GRANATE, "lw": 1.4})
            derecha.text(x + lado * 0.003, (1 + y) / 2, texto, ha="left" if lado > 0 else "right",
                         va="center", color=GRANATE, fontsize=9, fontweight="bold")


class FiguraComposicion(FiguraHallazgo):
    """Acto 2 · Contraste: la concentración cambia según la clasificación del glaciar."""

    nombre = "fig2_composicion_clasificacion"
    objetivo = "OE4 · ¿Cambia la concentración según la clasificación del glaciar?"
    grafico = "Barras apiladas al 100 % (número de glaciares frente a superficie)"
    tamano = (10, 4.4)

    def __init__(self, limpio, **kwargs):
        super().__init__(**kwargs)
        self._tabla = com.composicion(limpio, "CLASIFICA", "AREA_KM2")
        self._total_km2 = float(limpio["AREA_KM2"].sum())

    def _fila(self, tipo):
        return self._tabla.loc[tipo]

    def titulo(self):
        e = self._fila("GLACIAR EFLUENTE")
        return (f"{com.miles(e['glaciares'])} glaciares efluentes, el {com.pct(e['pct_glaciares'])} del total, "
                f"reúnen el {com.pct(e['pct_magnitud'])} de la superficie")

    def evidencia(self):
        e, g = self._fila("GLACIAR EFLUENTE"), self._fila("GLACIARETE")
        return (f"Efluentes: {com.miles(e['glaciares'])} glaciares ({com.pct(e['pct_glaciares'])}) y "
                f"{com.pct(e['pct_magnitud'])} de la superficie; glaciaretes: {com.miles(g['glaciares'])} "
                f"({com.pct(g['pct_glaciares'])}) y {com.pct(g['pct_magnitud'])}")

    def _dibujar(self, figura):
        eje = figura.subplots()
        filas = {"Número de glaciares\n(n = " + com.miles(self._tabla["glaciares"].sum()) + ")": "pct_glaciares",
                 "Superficie glaciar\n(" + com.miles(self._total_km2) + " km²)": "pct_magnitud"}
        posiciones = np.arange(len(filas))[::-1]
        for y, (etiqueta, columna) in zip(posiciones, filas.items()):
            izquierda = 0.0
            for tipo, fila in self._tabla.iterrows():
                ancho = fila[columna]
                color = COLORES_TIPO.get(tipo, GRIS)
                eje.barh(y, ancho, left=izquierda, color=color, edgecolor="white", height=0.62,
                         label=nombre_tipo(tipo) if y == posiciones[0] else None)
                if ancho >= 4:
                    claro = color in (GRANATE, AZUL, COLORES_TIPO["GLACIAR DE MONTAÑA"])
                    eje.text(izquierda + ancho / 2, y, com.pct(ancho), ha="center", va="center",
                             fontsize=9, color="white" if claro else TINTA, fontweight="bold")
                izquierda += ancho
        eje.set_yticks(posiciones, list(filas))
        eje.set_xlim(0, 100)
        _formato_pct_eje(eje.xaxis)
        eje.set_xlabel("Porcentaje del total")
        eje.spines["left"].set_visible(False)
        eje.tick_params(axis="y", length=0)
        eje.legend(ncols=5, loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=8.5,
                   title="Clasificación (ordenada por su aporte a la superficie)", title_fontsize=8.5)
        g = self._fila("GLACIARETE")
        eje.set_title(f"Los glaciaretes son el {com.pct(g['pct_glaciares'])} de los glaciares y aportan "
                      f"solo el {com.pct(g['pct_magnitud'])} de la superficie", color=TINTA, fontsize=10)


class FiguraTamanoPorTipo(FiguraHallazgo):
    """Acto 3 · Resolución: gran parte de la concentración se explica por el tipo de glaciar."""

    nombre = "fig3_tamano_por_clasificacion"
    objetivo = "OE4 · ¿Por qué cambia la concentración según la clasificación?"
    grafico = "Caja con puntos superpuestos, eje logarítmico, con el Gini de cada tipo"
    tamano = (10, 4.8)

    def __init__(self, limpio, magnitudes, semilla=42, **kwargs):
        super().__init__(**kwargs)
        self._datos = limpio[["CLASIFICA", "AREA_KM2"]].assign(CLASIFICA=lambda d: d["CLASIFICA"].astype(str))
        gini = com.gini_por_grupo(self._datos, "CLASIFICA")
        mediana = self._datos.groupby("CLASIFICA")["AREA_KM2"].median().rename("mediana_km2")
        self._tabla = gini.join(mediana).sort_values("mediana_km2", ascending=False)
        self._gini_total = float(magnitudes.set_index("magnitud").loc["AREA_KM2", "gini"])
        self._semilla = semilla

    def titulo(self):
        return (f"Cada tipo de glaciar ocupa su propio rango de tamaño: dentro de cada tipo el Gini baja a "
                f"{com.decimal(self._tabla['gini'].min(), 2)}–{com.decimal(self._tabla['gini'].max(), 2)}, "
                f"frente a {com.decimal(self._gini_total)} en el total")

    def evidencia(self):
        partes = [f"{nombre_tipo(t)}: mediana {com.decimal(f['mediana_km2'], 3)} km², Gini {com.decimal(f['gini'], 2)}"
                  for t, f in self._tabla.iterrows()]
        return f"Gini total {com.decimal(self._gini_total)}. " + "; ".join(partes)

    def _dibujar(self, figura):
        # La caja se dibuja con Matplotlib y no con sns.boxplot: seaborn 0.13.2 usa un argumento
        # que Matplotlib 3.11 declara obsoleto y el notebook mostraría una advertencia.
        eje = figura.subplots()
        orden = list(self._tabla.index)
        posiciones = np.arange(len(orden))
        valores = [self._datos.loc[self._datos["CLASIFICA"] == t, "AREA_KM2"].to_numpy() for t in orden]
        cajas = eje.boxplot(valores, positions=posiciones, orientation="horizontal", widths=0.55,
                            showfliers=False, patch_artist=True,
                            medianprops={"color": TINTA, "lw": 1.6}, whiskerprops={"color": GRIS},
                            capprops={"color": GRIS}, boxprops={"edgecolor": GRIS})
        for caja, tipo in zip(cajas["boxes"], orden):
            caja.set_facecolor(COLORES_TIPO.get(tipo, GRIS))
            caja.set_alpha(0.85)
        generador = np.random.default_rng(self._semilla)
        muestra = self._datos.sample(min(2500, len(self._datos)), random_state=self._semilla)
        y_muestra = muestra["CLASIFICA"].map({t: i for i, t in enumerate(orden)}).to_numpy(float)
        eje.scatter(muestra["AREA_KM2"], y_muestra + generador.uniform(-0.22, 0.22, len(muestra)),
                    s=2.5, color=TINTA, alpha=0.25, edgecolors="none", rasterized=True)
        eje.set_xscale("log")
        eje.invert_yaxis()
        formato_eje_km2(eje.xaxis)
        eje.set_yticks(range(len(orden)), [f"{nombre_tipo(t)}\n(n = {com.miles(self._tabla.loc[t, 'glaciares'])})"
                                           for t in orden])
        eje.set_xlabel("Superficie de cada glaciar (km², escala logarítmica)")
        eje.set_ylabel("")
        eje.grid(axis="x", color=HIELO, lw=0.8)
        for y, tipo in enumerate(orden):     # x en coordenadas del eje (1,01 = justo a la derecha)
            eje.text(1.01, y, f"Gini {com.decimal(self._tabla.loc[tipo, 'gini'], 2)}", va="center",
                     fontsize=9, color=GRANATE if tipo == "GLACIAR EFLUENTE" else TINTA, fontweight="bold",
                     transform=eje.get_yaxis_transform())
        eje.set_title("Caja: mediana y cuartiles · puntos: muestra aleatoria de 2.500 glaciares",
                      color=GRIS, fontsize=9)
