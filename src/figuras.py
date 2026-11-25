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
from abc import ABC, abstractmethod

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch
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
class FiguraHallazgo(ABC):
    """Contrato común de las figuras del informe. Clase abstracta (`abc.ABC`): no se instancia.

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
    @abstractmethod
    def _dibujar(self, figura):
        raise NotImplementedError(f"{type(self).__name__} debe implementar _dibujar()")

    @abstractmethod
    def titulo(self):
        """El hallazgo, con la cifra que lo respalda (no el tema del gráfico)."""
        raise NotImplementedError(f"{type(self).__name__} debe implementar titulo()")

    @abstractmethod
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
    grafico = "Barras pareadas: % de los glaciares y % de la superficie por clasificación"
    tamano = (10, 5)

    def __init__(self, limpio, **kwargs):
        super().__init__(**kwargs)
        self._tabla = com.composicion(limpio, "CLASIFICA", "AREA_KM2")
        self._total_km2 = float(limpio["AREA_KM2"].sum())

    def _fila(self, tipo):
        return self._tabla.loc[tipo]

    def titulo(self):
        e = self._fila("GLACIAR EFLUENTE")
        return (f"El {com.pct(e['pct_glaciares'])} de los glaciares, los efluentes, reúne el "
                f"{com.pct(e['pct_magnitud'])} de la superficie glaciar del país")

    def evidencia(self):
        e, g = self._fila("GLACIAR EFLUENTE"), self._fila("GLACIARETE")
        return (f"Efluentes: {com.miles(e['glaciares'])} glaciares ({com.pct(e['pct_glaciares'])}) y "
                f"{com.pct(e['pct_magnitud'])} de la superficie; glaciaretes: {com.miles(g['glaciares'])} "
                f"({com.pct(g['pct_glaciares'])}) y {com.pct(g['pct_magnitud'])}")

    def _dibujar(self, figura):
        eje = figura.subplots()
        tipos = list(self._tabla.index)
        y = np.arange(len(tipos))
        alto = 0.38
        glaciares = eje.barh(y - alto / 2, self._tabla["pct_glaciares"], height=alto, color=NEUTRO,
                             label=f"% de los glaciares (n = {com.miles(self._tabla['glaciares'].sum())})")
        colores = [GRANATE if t == "GLACIAR EFLUENTE" else AZUL for t in tipos]
        superficie = eje.barh(y + alto / 2, self._tabla["pct_magnitud"], height=alto, color=colores,
                              label=f"% de la superficie ({com.miles(self._total_km2)} km²)")
        for barras in (glaciares, superficie):
            eje.bar_label(barras, labels=[com.pct(v) for v in barras.datavalues], padding=4, fontsize=9,
                          color=TINTA)
        eje.set_yticks(y, [nombre_tipo(t) for t in tipos])
        eje.invert_yaxis()
        eje.set_xlim(0, 80)
        _formato_pct_eje(eje.xaxis)
        eje.set_xlabel("Porcentaje del total nacional")
        eje.tick_params(axis="y", length=0)
        eje.legend(handles=[Patch(color=NEUTRO, label=glaciares.get_label()),
                            Patch(color=AZUL, label=superficie.get_label()),
                            Patch(color=GRANATE, label="% de la superficie de los efluentes (destacado)")],
                   loc="lower right", fontsize=9)
        eje.grid(axis="x", color=HIELO, lw=0.6)
        g = self._fila("GLACIARETE")
        eje.set_title(f"Arriba de cada par, su peso en número; abajo, en superficie. Los glaciaretes son el "
                      f"{com.pct(g['pct_glaciares'])} de los glaciares y aportan el {com.pct(g['pct_magnitud'])}",
                      color=GRIS, fontsize=9)


class FiguraTheil(FiguraHallazgo):
    """Acto 3 · Resolución: qué parte de la desigualdad se asocia a la clasificación y cuál a la región."""

    nombre = "fig3_descomposicion_theil"
    objetivo = "OE4 · ¿Qué parte de la concentración se asocia a la clasificación y cuál a la región?"
    grafico = "Barras apiladas al 100 %: desigualdad entre y dentro de los grupos (descomposición de Theil)"
    tamano = (10, 4.2)

    def __init__(self, limpio, **kwargs):
        super().__init__(**kwargs)
        self._tabla = com.descomposicion_theil(limpio)

    def titulo(self):
        c, r = self._tabla.loc["Clasificación"], self._tabla.loc["Región"]
        return (f"La clasificación da cuenta del {com.pct(c['pct_entre'])} de la desigualdad de la superficie; "
                f"la región, solo del {com.pct(r['pct_entre'])}")

    def evidencia(self):
        t = self._tabla
        plural = {"Clasificación": "clasificaciones", "Macrozona": "macrozonas", "Región": "regiones"}
        partes = [f"entre {plural.get(n, n.lower())} {com.pct(f['pct_entre'])}" for n, f in t.iterrows()]
        return f"Theil de la superficie {com.decimal(t['theil_total'].iloc[0])}; " + "; ".join(partes)

    def _dibujar(self, figura):
        eje = figura.subplots()
        t = self._tabla
        y = np.arange(len(t))
        colores = [GRANATE if n == "Clasificación" else AZUL for n in t.index]
        eje.barh(y, t["pct_entre"], color=colores, height=0.55, label="Entre los grupos")
        eje.barh(y, t["pct_dentro"], left=t["pct_entre"], color=HIELO, height=0.55, label="Dentro de los grupos")
        for i, (_, f) in enumerate(t.iterrows()):
            eje.text(f["pct_entre"] + 1 if f["pct_entre"] < 12 else f["pct_entre"] / 2, i, com.pct(f["pct_entre"]),
                     ha="left" if f["pct_entre"] < 12 else "center", va="center", fontsize=10, fontweight="bold",
                     color=TINTA if f["pct_entre"] < 12 else "white")
            eje.text(99, i, f"dentro: {com.pct(f['pct_dentro'])}", ha="right", va="center", fontsize=9.5, color=TINTA)
        eje.set_yticks(y, [f"{n}\n({int(f['grupos'])} grupos)" for n, f in t.iterrows()])
        eje.invert_yaxis()
        eje.set_xlim(0, 100)
        _formato_pct_eje(eje.xaxis)
        eje.set_xlabel("Porcentaje del índice de Theil de la superficie")
        eje.tick_params(axis="y", length=0)
        eje.legend(handles=[Patch(color=AZUL, label="Entre los grupos (en granate, la clasificación)"),
                            Patch(color=HIELO, label="Dentro de los grupos")],
                   ncols=2, loc="upper center", bbox_to_anchor=(0.5, -0.22), fontsize=9)
        eje.set_title(f"Índice de Theil de la superficie: {com.decimal(t['theil_total'].iloc[0])}, separado en desigualdad "
                      "entre grupos y dentro de ellos (asociación, no causa)", color=GRIS, fontsize=9)


# ====================================================================== figuras complementarias
class FiguraTamanoPorTipo(FiguraHallazgo):
    """Complementaria · Por qué los tipos difieren: cada uno ocupa su propio rango de tamaño."""

    nombre = "fig4_tamano_por_clasificacion"
    rol = "complementaria"
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


class FiguraRegiones(FiguraHallazgo):
    """Complementaria · Concentración geográfica: dos regiones reúnen casi toda la superficie."""

    nombre = "fig5_superficie_por_region"
    rol = "complementaria"
    objetivo = "OE3 · ¿Qué tan concentrada está la superficie glaciar en pocas regiones?"
    grafico = "Barras horizontales ordenadas, con las dos mayores destacadas"
    tamano = (9, 6)

    def __init__(self, limpio, **kwargs):
        super().__init__(**kwargs)
        self._tabla = com.composicion(limpio, "REGION", "AREA_KM2")

    def titulo(self):
        dos = self._tabla.iloc[:2]
        return (f"{nombre_region(dos.index[0])} y {nombre_region(dos.index[1])} reúnen el "
                f"{com.pct(dos['pct_magnitud'].sum())} de la superficie glaciar del país")

    def evidencia(self):
        dos = self._tabla.iloc[:2]
        return "; ".join(f"{nombre_region(r)}: {com.pct(f['pct_magnitud'])} con {com.miles(f['glaciares'])} glaciares"
                         for r, f in dos.iterrows()) + f"; las otras {len(self._tabla) - 2} regiones: " \
            f"{com.pct(self._tabla['pct_magnitud'].iloc[2:].sum())}"

    def _dibujar(self, figura):
        eje = figura.subplots()
        t = self._tabla.iloc[::-1]
        colores = [GRANATE if r in self._tabla.index[:2] else NEUTRO for r in t.index]
        barras = eje.barh([nombre_region(r) for r in t.index], t["pct_magnitud"], color=colores, height=0.7)
        etiquetas = [f"{com.pct(p, 1 if p >= 0.1 else 2)}  ({com.miles(n)} glaciares)"
                     for p, n in zip(t["pct_magnitud"], t["glaciares"])]
        eje.bar_label(barras, labels=etiquetas, padding=3, fontsize=8.5, color=TINTA)
        eje.set_xlim(0, 68)
        _formato_pct_eje(eje.xaxis)
        eje.set_xlabel("Porcentaje de la superficie glaciar nacional")
        eje.tick_params(axis="y", length=0)
        eje.set_title("Regiones ordenadas por su aporte; entre paréntesis, cuántos glaciares tiene cada una",
                      color=GRIS, fontsize=9)


class FiguraVolumenDerivado(FiguraHallazgo):
    """Complementaria · Magnitud secundaria: por qué el volumen está más concentrado que la superficie."""

    nombre = "fig7_volumen_derivado"
    rol = "complementaria"
    objetivo = "OE3 · ¿Por qué el volumen está más concentrado que la superficie?"
    grafico = "Dispersión log-log con recta de igualdad"
    tamano = (8, 6)

    def __init__(self, limpio, magnitudes, **kwargs):
        super().__init__(**kwargs)
        self._tabla = pd.DataFrame({
            "CLASIFICA": limpio["CLASIFICA"].astype(str).to_numpy(),
            "publicado": limpio["VOL_km3"].to_numpy(float),
            "desde_area": con.volumen_desde_area(limpio).to_numpy(float),
        })
        positivos = self._tabla[(self._tabla["publicado"] > 0) & (self._tabla["desde_area"] > 0)]
        self._correlacion_log = float(np.corrcoef(np.log10(positivos["publicado"]),
                                                  np.log10(positivos["desde_area"]))[0, 1])
        self._magnitudes = magnitudes.set_index("magnitud")

    def titulo(self):
        m = self._magnitudes
        veces = 10 ** con.EXPONENTE_VOLUMEN
        return (f"El volumen se calculó desde el área con exponente {com.decimal(con.EXPONENTE_VOLUMEN)}: un glaciar 10 "
                f"veces mayor tiene {veces:.0f} veces más volumen, y el Gini sube de "
                f"{com.decimal(m.loc['AREA_KM2', 'gini'])} a {com.decimal(m.loc['VOL_km3', 'gini'])}")

    def evidencia(self):
        m = self._magnitudes
        return (f"Gini {com.decimal(m.loc['AREA_KM2', 'gini'])} (superficie) → {com.decimal(m.loc['VOL_km3', 'gini'])} "
                f"(volumen); 1 % mayor {com.pct(m.loc['AREA_KM2', 'pct_1%_mayores'])} → "
                f"{com.pct(m.loc['VOL_km3', 'pct_1%_mayores'])}; correlación (log10) con el volumen calculado solo "
                f"desde el área {com.decimal(self._correlacion_log, 4)}")

    def _dibujar(self, figura):
        eje = figura.subplots()
        t = self._tabla[(self._tabla["publicado"] > 0) & (self._tabla["desde_area"] > 0)]
        rocoso = t["CLASIFICA"] == "GLACIAR ROCOSO"
        eje.scatter(t.loc[~rocoso, "desde_area"], t.loc[~rocoso, "publicado"], s=4, alpha=0.3, color=AZUL,
                    edgecolors="none", rasterized=True, label=f"Glaciares de hielo (n = {com.miles((~rocoso).sum())})")
        eje.scatter(t.loc[rocoso, "desde_area"], t.loc[rocoso, "publicado"], s=4, alpha=0.4,
                    color=COLORES_TIPO["GLACIAR ROCOSO"], edgecolors="none", rasterized=True,
                    label=f"Glaciares rocosos, × 0,6 (n = {com.miles(rocoso.sum())})")
        extremos = [t[["publicado", "desde_area"]].min().min(), t[["publicado", "desde_area"]].max().max()]
        eje.plot(extremos, extremos, color=GRANATE, lw=1.4, ls="--", label="Igualdad (volumen publicado = calculado)")
        eje.set_xscale("log")
        eje.set_yscale("log")
        eje.set_xlabel("Volumen calculado solo desde el área: 0,0285 · ÁREA^1,357 (km³)")
        eje.set_ylabel("Volumen publicado por la DGA (km³)")
        leyenda = eje.legend(loc="upper left", fontsize=8.5, markerscale=3)
        for marca in leyenda.legend_handles:
            marca.set_alpha(1)
        eje.grid(color=HIELO, lw=0.6)
        eje.set_title(f"Cada punto es un glaciar · correlación de los logaritmos: {com.decimal(self._correlacion_log, 4)}",
                      color=GRIS, fontsize=9)


class FiguraTipoPorMacrozona(FiguraHallazgo):
    """Complementaria · Control por una tercera variable: ¿el patrón por tipo se mantiene por zona?"""

    nombre = "fig6_tipo_por_macrozona"
    rol = "complementaria"
    objetivo = "OE4 · ¿El efecto de la clasificación se mantiene al separar por macrozona?"
    grafico = "Mapa de calor de una tabla cruzada (porcentaje de la fila)"
    tamano = (10, 4.6)

    def __init__(self, limpio, **kwargs):
        super().__init__(**kwargs)
        tabla = com.participacion_cruzada(limpio, "MZON_GLAC", "CLASIFICA")
        orden_tipos = com.composicion(limpio, "CLASIFICA").index
        self._tabla = tabla[list(orden_tipos)]
        self._gini = com.gini_por_grupo(limpio, "MZON_GLAC")

    def _dominante(self, zona):
        fila = self._tabla.loc[zona]
        return fila.idxmax(), float(fila.max())

    def titulo(self):
        tipo, valor = self._dominante("MACROZONA AUSTRAL")
        return (f"El tipo que domina la superficie cambia con la latitud: los efluentes solo existen en la "
                f"macrozona austral, donde reúnen el {com.pct(valor)}")

    def evidencia(self):
        partes = []
        for zona in self._tabla.index:
            tipo, valor = self._dominante(zona)
            partes.append(f"{zona.title()}: {nombre_tipo(tipo).lower()} {com.pct(valor)} "
                          f"(Gini {com.decimal(self._gini.loc[str(zona), 'gini'], 2)})")
        return "; ".join(partes)

    def _dibujar(self, figura):
        eje = figura.subplots()
        anotaciones = self._tabla.map(lambda v: "—" if v == 0 else "< 0,1" if v < 0.05 else com.pct(v, 1).replace(" %", ""))
        sns.heatmap(self._tabla, annot=anotaciones, fmt="", cmap="Blues", vmin=0, vmax=100, linewidths=1,
                    linecolor="white", cbar_kws={"label": "% de la superficie de la macrozona",
                                                 "format": PercentFormatter(100, decimals=0)}, ax=eje)
        eje.set_xticks(np.arange(self._tabla.shape[1]) + 0.5,
                       [nombre_tipo(t).replace("Glaciar ", "Glaciar\n") for t in self._tabla.columns], rotation=0)
        eje.set_yticks(np.arange(self._tabla.shape[0]) + 0.5,
                       [f"{str(z).title().replace('Macrozona ', '')}\nGini {com.decimal(self._gini.loc[str(z), 'gini'], 2)}"
                        for z in self._tabla.index], rotation=0)
        eje.set_xlabel("")
        eje.set_ylabel("Macrozona (de norte a sur)")
        eje.set_title("Cada fila suma 100 %; «—» indica que el tipo no existe en esa macrozona",
                      color=GRIS, fontsize=9)