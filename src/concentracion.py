"""Concentración de la superficie glaciar y del volumen como magnitud derivada (Fase 3).

Resultado principal del proyecto: cuán concentrada está la SUPERFICIE (AREA_KM2) en pocos
glaciares, regiones y clasificaciones. El volumen (VOL_km3) no es una medición: la DGA lo estimó
desde el área (Chen y Ohmura, 1990; verificado en F2 sección 2.3), de modo que

    VOL ≈ 0,0285 · AREA^1,357   (× 0,6 en glaciares rocosos)

Su concentración es una consecuencia de la de la superficie, amplificada por el exponente
1,357 > 1 (un glaciar 10 veces mayor tiene unas 23 veces más volumen), y no un hallazgo
independiente. `comparar_magnitudes` lo demuestra: el volumen calculado solo con el área
reproduce la concentración del volumen del inventario.

Diseño (mismo contrato que transformadores.py):
- `MedidaConcentracion`: clase base con el método plantilla `calcular`, que valida una sola vez
  y delega en `_calcular`.
- `ParticipacionMayores`, `IndiceGini`, `CurvaLorenz` e `IndiceTheil` (F4): clases hijas (herencia).
- `descomponer_theil` (F4): separa la desigualdad en una parte entre grupos y otra dentro de ellos,
  algo que el Gini no permite hacer de forma exacta.
- `AnalisisConcentracion` aplica cualquier lista de medidas sin preguntar su tipo (polimorfismo);
  agregar una medida nueva no modifica esta clase.
- El estado interno lleva guion bajo y se lee mediante propiedades (encapsulamiento).
"""

import numpy as np
import pandas as pd

MAGNITUDES = {"AREA_KM2": "superficie (km²)", "VOL_km3": "volumen (km³)", "VOL_DESDE_AREA": "volumen desde el área (km³)"}
COEFICIENTE_VOLUMEN = 0.0285      # 28,5 m · km² / 1000 → km³ (F2 sección 2.3)
EXPONENTE_VOLUMEN = 1.357         # 1 (área) + 0,357 (espesor de Chen y Ohmura)
FACTOR_HIELO = {"GLACIAR ROCOSO": 0.60}   # fracción de hielo; resto de clasificaciones = 1


# medidas
class MedidaConcentracion:
    """Clase base: el contrato común de toda medida de concentración. No se usa directamente."""

    etiqueta = "sin definir"

    def calcular(self, valores):
        """Valida `valores` y delega el cálculo en `_calcular` (método plantilla).

        Lanza ValueError si `valores` está vacío, tiene nulos, negativos o suma cero.
        """
        arreglo = np.asarray(valores, dtype=float)
        if arreglo.size == 0:
            raise ValueError(f"{self.etiqueta}: no hay valores")
        if np.isnan(arreglo).any():
            raise ValueError(f"{self.etiqueta}: hay valores nulos")
        if (arreglo < 0).any():
            raise ValueError(f"{self.etiqueta}: hay valores negativos")
        if arreglo.sum() == 0:
            raise ValueError(f"{self.etiqueta}: el total es cero")
        return self._calcular(arreglo)

    def _calcular(self, valores):
        """Recibe un arreglo ya validado. Lo implementa cada clase hija."""
        raise NotImplementedError(f"{type(self).__name__} debe implementar _calcular()")

    def __repr__(self):
        return f"{type(self).__name__}()"


class ParticipacionMayores(MedidaConcentracion):
    """% del total que reúne la fracción `fraccion` de glaciares con mayor valor.

    Coincide con F2 (sección 2.2.1): se toman n = int(len · fraccion) glaciares. Sobre 26.180
    glaciares, fraccion = 0,01 son los 261 mayores.
    """

    def __init__(self, fraccion):
        if not 0 < fraccion <= 1:
            raise ValueError(f"La fracción debe estar en (0, 1] y se recibió {fraccion}")
        self._fraccion = fraccion

    @property
    def fraccion(self):
        return self._fraccion

    @property
    def etiqueta(self):
        return f"pct_{self._fraccion:.0%}_mayores"

    def _calcular(self, valores):
        n = int(len(valores) * self._fraccion)
        if n == 0:
            raise ValueError(f"{self.etiqueta}: {len(valores)} valores no alcanzan para un glaciar")
        mayores = np.partition(valores, len(valores) - n)[len(valores) - n:]   # O(n): no ordena todo
        return float(100 * mayores.sum() / valores.sum())

    def __repr__(self):
        return f"{type(self).__name__}({self._fraccion})"


class IndiceGini(MedidaConcentracion):
    """Coeficiente de Gini: 0 = todos iguales; (n − 1)/n = un glaciar concentra todo.

    Fórmula sobre los valores ordenados de menor a mayor (x₁ ≤ … ≤ xₙ):

        G = 2 · Σ(i · xᵢ) / (n · Σ xᵢ) − (n + 1) / n,    i = 1..n

    Costo O(n log n) por el ordenamiento y O(n) de memoria. La definición por pares,
    Σᵢ Σⱼ |xᵢ − xⱼ| / (2 n² x̄), da el mismo valor en O(n²); medicion.py compara ambas.
    """

    etiqueta = "gini"

    def _calcular(self, valores):
        x = np.sort(valores)
        n = len(x)
        rangos = np.arange(1, n + 1)
        return float(2 * np.dot(rangos, x) / (n * x.sum()) - (n + 1) / n)


class CurvaLorenz(MedidaConcentracion):
    """Curva de Lorenz: proporción acumulada de glaciares (de menor a mayor) frente a la
    proporción acumulada de la magnitud. Empieza en (0, 0) y termina en (1, 1).

    `puntos` submuestrea la curva para graficarla sin dibujar 26.180 puntos.
    """

    etiqueta = "lorenz"

    def __init__(self, puntos=201):
        if int(puntos) < 2:
            raise ValueError("La curva necesita al menos 2 puntos")
        self._puntos = int(puntos)

    def _calcular(self, valores):
        x = np.sort(valores)
        acumulada = np.concatenate([[0.0], np.cumsum(x) / x.sum()])
        proporcion = np.linspace(0, 1, len(acumulada))
        posiciones = np.unique(np.linspace(0, len(acumulada) - 1, self._puntos).round().astype(int))
        return pd.DataFrame({"prop_glaciares": proporcion[posiciones], "prop_magnitud": acumulada[posiciones]})


class IndiceTheil(MedidaConcentracion):
    """Índice de Theil T: 0 = todos iguales; ln(n) = un glaciar concentra todo.

        T = (1/n) · Σ (xᵢ/μ) · ln(xᵢ/μ),    con 0 · ln 0 = 0

    A diferencia del Gini, se descompone exactamente en una parte ENTRE grupos y otra DENTRO de
    los grupos (ver `descomponer_theil`). Costo O(n) en tiempo y memoria.
    """

    etiqueta = "theil"

    def _calcular(self, valores):
        r = valores / valores.mean()
        return float(np.mean(np.where(r > 0, r * np.log(np.where(r > 0, r, 1.0)), 0.0)))


# análisis
class AnalisisConcentracion:
    """Aplica una lista de medidas a una magnitud (AREA_KM2 o VOL_km3), total y por grupo."""

    GRUPOS = ("REGION", "CLASIFICA", "MZON_GLAC")

    def __init__(self, df, magnitud, medidas):
        if magnitud not in df.columns:
            raise KeyError(f"La magnitud {magnitud} no existe en el conjunto")
        if not medidas or not all(isinstance(m, MedidaConcentracion) for m in medidas):
            raise TypeError("AnalisisConcentracion requiere una lista no vacía de MedidaConcentracion")
        columnas = [magnitud, *[g for g in self.GRUPOS if g in df.columns]]
        self._datos = df[columnas].copy()          # copia: el análisis no depende de cambios externos
        self._magnitud = magnitud
        self._medidas = list(medidas)

    @property
    def magnitud(self):
        return self._magnitud

    @property
    def medidas(self):
        return tuple(self._medidas)

    def resumen(self):
        """{magnitud, glaciares, total, <etiqueta>: valor} con las medidas escalares."""
        valores = self._datos[self._magnitud].to_numpy()
        fila = {"magnitud": self._magnitud, "glaciares": len(valores), "total": float(valores.sum())}
        for medida in self._medidas:                       # polimorfismo
            resultado = medida.calcular(valores)
            if not isinstance(resultado, pd.DataFrame):    # la curva de Lorenz se pide con curva()
                fila[medida.etiqueta] = resultado
        return fila

    def curva(self, puntos=201):
        return CurvaLorenz(puntos).calcular(self._datos[self._magnitud].to_numpy())

    def por_grupo(self, grupo):
        """% del total que aporta cada grupo, de mayor a menor, con el % acumulado, la cantidad
        de glaciares y las medidas escalares calculadas dentro de cada grupo."""
        if grupo not in self._datos.columns:
            raise KeyError(f"El grupo {grupo} no existe; opciones: {[g for g in self.GRUPOS if g in self._datos]}")
        suma = self._datos.groupby(grupo, observed=True)[self._magnitud].agg(["sum", "size"])
        tabla = pd.DataFrame({"glaciares": suma["size"], "total": suma["sum"],
                              "pct": 100 * suma["sum"] / suma["sum"].sum()})
        for medida in self._medidas:
            if isinstance(medida, CurvaLorenz):
                continue
            tabla[medida.etiqueta] = self._datos.groupby(grupo, observed=True)[self._magnitud].apply(
                lambda v, m=medida: m.calcular(v) if int(len(v) * getattr(m, "fraccion", 1)) > 0 else np.nan)
        tabla = tabla.sort_values("pct", ascending=False)
        tabla.insert(3, "pct_acumulado", tabla["pct"].cumsum())
        return tabla


#  descomposición de la desigualdad
def descomponer_theil(df, grupo, magnitud="AREA_KM2"):
    """Separa el Theil total en una parte entre grupos y otra dentro de los grupos.

        T = T_entre + T_dentro
        T_entre  = Σ_g s_g · ln(μ_g / μ)        (desigualdad si cada glaciar tuviera la media de su grupo)
        T_dentro = Σ_g s_g · T_g                (desigualdad dentro de cada grupo, ponderada)

    donde s_g es la fracción de la magnitud total que aporta el grupo g y μ_g su media. `pct_entre`
    es la parte de la desigualdad total de la que da cuenta el agrupamiento: una medida de asociación,
    no de causa.

    Lanza KeyError si falta la columna y ValueError (vía IndiceTheil) si la magnitud no es válida.
    """
    faltan = [c for c in (grupo, magnitud) if c not in df.columns]
    if faltan:
        raise KeyError(f"Columnas inexistentes: {faltan}")
    theil = IndiceTheil()
    valores = df[magnitud].to_numpy(dtype=float)
    total, media, suma = theil.calcular(valores), valores.mean(), valores.sum()
    entre = dentro = 0.0
    for _, sub in df.groupby(grupo, observed=True)[magnitud]:
        v = sub.to_numpy(dtype=float)
        s_g = v.sum() / suma
        if s_g > 0:
            entre += s_g * np.log(v.mean() / media)
            dentro += s_g * theil.calcular(v)
    return {"grupo": grupo, "grupos": int(df[grupo].nunique()), "theil_total": total,
            "entre": float(entre), "dentro": float(dentro),
            "pct_entre": float(100 * entre / total), "pct_dentro": float(100 * dentro / total)}


# relación área → volumen
def volumen_desde_area(df):
    """Volumen calculado SOLO con la superficie: 0,0285 · AREA^1,357 · factor de hielo."""
    factor = df["CLASIFICA"].astype(str).map(FACTOR_HIELO).fillna(1.0)
    return COEFICIENTE_VOLUMEN * df["AREA_KM2"] ** EXPONENTE_VOLUMEN * factor


def comparar_magnitudes(df, medidas):
    """Una fila por magnitud: superficie, volumen del inventario y volumen calculado desde el área.

    Es la evidencia de que la concentración del volumen deriva de la de la superficie: el volumen
    calculado solo con el área reproduce la del inventario.
    """
    magnitudes = pd.DataFrame({"AREA_KM2": df["AREA_KM2"], "VOL_km3": df["VOL_km3"],
                               "VOL_DESDE_AREA": volumen_desde_area(df)})
    return pd.DataFrame([AnalisisConcentracion(magnitudes, m, medidas).resumen() for m in magnitudes])


def medidas_proyecto():
    """Las medidas que responde la pregunta de investigación: 1 % y 10 % mayores y Gini."""
    return [ParticipacionMayores(0.01), ParticipacionMayores(0.10), IndiceGini()]