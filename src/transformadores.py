"""Transformadores del pipeline de F2: una clase base y una clase hija por paso.

`Transformador` aplica el método plantilla: define una sola vez el esqueleto de todo paso
(validar la entrada, aprender, controlar el estado, copiar antes de modificar y comprobar que no
se pierden filas) y delega en cada clase hija solo lo que cambia: qué aprende (`aprender`) y
cómo lo aplica (`aplicar`).

- Encapsulamiento: lo aprendido vive en `_parametros` y el control de orden en `_ajustado`;
  desde fuera solo se leen copias mediante las propiedades `parametros` y `evidencia`.
- Herencia: las clases hijas no repiten la validación ni el control de estado.
- Polimorfismo: el `Pipeline` llama `ajustar` y `transformar` sin preguntar el tipo de paso.

Los pasos aprenden del conjunto con `ajustar` y lo aplican con `transformar`. En este proyecto
(análisis descriptivo del inventario completo) se ajusta y transforma el mismo conjunto, lo que
reproduce F2; la separación deja los pasos listos para un esquema entrenamiento/prueba en F4.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

import imputacion as imp
import limpieza as lim
import utilidades as utl


class Transformador:
    """Clase base: el contrato común de todos los pasos. No se usa directamente."""

    def __init__(self, columnas=()):
        self._columnas = tuple(columnas)   # columnas que el paso necesita en la entrada
        self._parametros = {}              # lo que el paso aprende en ajustar()
        self._evidencia = {}               # cifras de la última aplicación (para la bitácora)
        self._ajustado = False             # impide transformar antes de ajustar

    # ------------------------------------------------------------ acceso de solo lectura
    @property
    def nombre(self):
        return type(self).__name__

    @property
    def parametros(self):
        return dict(self._parametros)      # copia defensiva: el estado interno no se expone

    @property
    def evidencia(self):
        return dict(self._evidencia)

    @property
    def ajustado(self):
        return self._ajustado

    # ------------------------------------------------------------------ método plantilla
    def ajustar(self, df):
        """Aprende los parámetros del conjunto recibido. Devuelve self para encadenar."""
        self._validar(df)
        self._parametros = self.aprender(df)
        self._ajustado = True
        return self

    def transformar(self, df):
        """Aplica lo aprendido sobre una copia de `df`; la entrada nunca se modifica."""
        if not self._ajustado:
            raise RuntimeError(f"{self.nombre}: hay que ajustar antes de transformar")
        self._validar(df)
        resultado = self.aplicar(df.copy())
        if len(resultado) != len(df):
            raise utl.ProyectoError(f"{self.nombre} cambió el número de filas: {len(df)} → {len(resultado)}")
        return resultado

    def ajustar_transformar(self, df):
        return self.ajustar(df).transformar(df)

    def _validar(self, df):
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"{self.nombre}: se esperaba un DataFrame y se recibió {type(df).__name__}")
        faltan = [c for c in self._columnas if c not in df.columns]
        if faltan:
            raise KeyError(f"{self.nombre}: faltan las columnas {faltan}")

    # ------------------------------------------------ lo que cada clase hija implementa
    def aprender(self, df):
        """Devuelve el diccionario de parámetros. Lo implementa cada clase hija."""
        raise NotImplementedError(f"{self.nombre} debe implementar aprender()")

    def aplicar(self, df):
        """Transforma `df` (ya copiado) y lo devuelve. Lo implementa cada clase hija."""
        raise NotImplementedError(f"{self.nombre} debe implementar aplicar()")

    def __repr__(self):
        estado = "ajustado" if self._ajustado else "sin ajustar"
        return f"{self.nombre}({', '.join(self._columnas)}) [{estado}]"


# ================================================================= limpieza (F2 sec. 3)
class DescartadorColumnas(Transformador):
    """Descarta columnas sin información, las redundantes declaradas y convierte una columna
    casi vacía en bandera binaria (CH_CASQ → EN_CAMPO_HIELO: el faltante significa «no pertenece»)."""

    def __init__(self, umbral_faltantes=0.60, redundantes=("WGI_1", "OBJECTID"),
                 a_bandera=("CH_CASQ", "EN_CAMPO_HIELO")):
        super().__init__(columnas=[*redundantes, a_bandera[0]])
        self.umbral_faltantes = umbral_faltantes
        self.redundantes = list(redundantes)
        self.origen_bandera, self.bandera = a_bandera

    def aprender(self, df):
        sin_info = lim.columnas_sin_informacion(df, self.umbral_faltantes)
        descartar = [c for c in sin_info["variable"] if c != self.origen_bandera] + self.redundantes
        return {"descartar": descartar + [self.origen_bandera], "sin_informacion": sin_info.to_dict("records")}

    def aplicar(self, df):
        df[self.bandera] = df[self.origen_bandera].notna().astype(int)
        df = lim.eliminar_columnas(df, self._parametros["descartar"])
        self._evidencia = {"descartadas": len(self._parametros["descartar"]), self.bandera: int(df[self.bandera].sum())}
        return df


class NormalizadorTexto(Transformador):
    """Repara la codificación, pasa a mayúsculas y colapsa espacios. Aprende qué columnas son texto."""

    def __init__(self, excluir=("COD_GLA", "LATITUD", "LONGITUD", "FUEN_FECHA")):
        super().__init__()
        self.excluir = tuple(excluir)

    def aprender(self, df):
        return {"columnas": lim.columnas_texto(df, self.excluir)}

    def aplicar(self, df):
        cambios = {}
        for columna in self._parametros["columnas"]:
            if columna not in df.columns:
                continue
            nueva = lim.normalizar_texto(df[columna])
            n = int((nueva.fillna("") != df[columna].fillna("")).sum())
            if n:
                cambios[columna] = n
            df[columna] = nueva
        self._evidencia = {"valores_corregidos": sum(cambios.values()), "por_columna": cambios}
        return df


class ConversorTipos(Transformador):
    """Coordenadas con coma decimal a float, fecha en formatos mixtos a fecha + año y códigos a texto."""

    def __init__(self, coordenadas=("LATITUD", "LONGITUD"), fecha="FUEN_FECHA", codigos=tuple(utl.COLUMNAS_CODIGO)):
        super().__init__(columnas=[*coordenadas, fecha, *codigos])
        self.coordenadas, self.fecha, self.codigos = list(coordenadas), fecha, list(codigos)

    def aprender(self, df):
        # No hay nada que estimar: se registran las reglas de conversión que se aplicarán
        return {"coordenadas": self.coordenadas, "fecha": f"{self.fecha} → {self.fecha} + FUEN_ANIO",
                "codigos_a_texto": self.codigos}

    def aplicar(self, df):
        for columna in self.coordenadas:
            df[columna] = lim.convertir_decimal_coma(df[columna])
        df[self.fecha], df["FUEN_ANIO"] = lim.parsear_fecha_mixta(df[self.fecha])
        df[self.codigos] = df[self.codigos].astype("string")
        self._evidencia = {"coordenadas_nulas": int(df[self.coordenadas].isna().sum().sum()),
                           "fechas_completas": int(df[self.fecha].notna().sum()),
                           "anios": int(df["FUEN_ANIO"].notna().sum())}
        return df


class ReconstructorVolumen(Transformador):
    """Recalcula VOL_km3 = 0 y EQ_AGUAKM3 = 0 (redondeo de la fuente) con la fórmula del inventario.

    `aprender` verifica en los datos que los factores declarados son los de la DGA: la razón
    mediana VOL / (AREA·ESP/1000) y EQ / VOL por clasificación debe coincidir con ellos.
    """

    def __init__(self, factor_hielo=None, factor_agua=None, tolerancia=0.01, minimo=1e-3):
        super().__init__(columnas=["CLASIFICA", "AREA_KM2", "ESP_MED", "VOL_km3", "EQ_AGUAKM3"])
        self.factor_hielo = {"GLACIAR ROCOSO": 0.60} if factor_hielo is None else factor_hielo   # resto = 1
        self.factor_agua = {"GLACIAR ROCOSO": 0.917} if factor_agua is None else factor_agua     # resto = 0,85
        self.tolerancia, self.minimo = tolerancia, minimo

    def aprender(self, df):
        sub = df[df["VOL_km3"] >= self.minimo]
        razones = pd.DataFrame({
            "volumen": sub["VOL_km3"] / (sub["AREA_KM2"] * sub["ESP_MED"] / 1000),
            "agua": sub["EQ_AGUAKM3"] / sub["VOL_km3"],
        }).groupby(sub["CLASIFICA"]).median()
        for clase, fila in razones.iterrows():
            esperado_v, esperado_a = self.factor_hielo.get(clase, 1.0), self.factor_agua.get(clase, 0.85)
            if abs(fila["volumen"] - esperado_v) >= self.tolerancia or abs(fila["agua"] - esperado_a) >= self.tolerancia:
                raise utl.ProyectoError(f"{clase}: razones observadas {fila.round(4).to_dict()} ≠ factores declarados")
        return {"factor_hielo": dict(self.factor_hielo), "factor_agua": dict(self.factor_agua),
                "razones_observadas": razones.round(4).to_dict("index")}

    def aplicar(self, df):
        f_hielo = df["CLASIFICA"].map(self._parametros["factor_hielo"]).fillna(1.0)
        f_agua = df["CLASIFICA"].map(self._parametros["factor_agua"]).fillna(0.85)
        vol0 = df["VOL_km3"] == 0
        df.loc[vol0, "VOL_km3"] = (df["AREA_KM2"] * df["ESP_MED"] / 1000 * f_hielo)[vol0]
        eq0 = df["EQ_AGUAKM3"] == 0
        df.loc[eq0, "EQ_AGUAKM3"] = (df["VOL_km3"] * f_agua)[eq0]
        df["VOL_RECALCULADO"] = vol0.astype(int)
        df["EQ_RECALCULADO"] = eq0.astype(int)
        self._evidencia = {"volumenes": int(vol0.sum()), "equivalentes": int(eq0.sum())}
        return df


class MarcadorFaltantes(Transformador):
    """Convierte en NaN los faltantes encubiertos de altitud para tratarlos explícitamente:
    HMIN = 0 sin frente en fiordo (implausible) y HMEDIA < HMIN (incoherente)."""

    def __init__(self):
        super().__init__(columnas=["HMIN", "HMEDIA", "FRENTE_TER"])

    def aprender(self, df):
        return {"reglas": ["HMIN = 0 y FRENTE_TER ≠ FIORDO → HMIN = NaN", "HMEDIA < HMIN → HMEDIA = NaN"]}

    def aplicar(self, df):
        hmin0 = (df["HMIN"] == 0) & (df["FRENTE_TER"] != "FIORDO")
        df.loc[hmin0, "HMIN"] = np.nan
        incoherente = df["HMEDIA"] < df["HMIN"]
        df.loc[incoherente, "HMEDIA"] = np.nan
        self._evidencia = {"HMIN": int(hmin0.sum()), "HMEDIA": int(incoherente.sum())}
        return df


class ImputadorEstrategia(Transformador):
    """Imputa `columna` con una estrategia inyectada (patrón Strategy).

    Con una sola estrategia la usa directamente. Con varias, `aprender` las compara (sobre las filas
    con `limite_superior` conocido) y elige con la regla declarada en F2: sin pérdida de filas, sin
    violaciones de `columna ≤ limite_superior` y menor cambio de la desviación estándar.
    """

    def __init__(self, columna, estrategias, limite_superior=None):
        estrategias = estrategias if isinstance(estrategias, (list, tuple)) else [estrategias]
        if not estrategias or not all(isinstance(e, imp.EstrategiaImputacion) for e in estrategias):
            raise TypeError("ImputadorEstrategia requiere una o más EstrategiaImputacion")
        if len(estrategias) > 1 and limite_superior is None:
            raise ValueError("Para comparar estrategias hay que indicar `limite_superior`")
        super().__init__(columnas=[columna] + ([limite_superior] if limite_superior else []))
        self.columna, self.limite_superior = columna, limite_superior
        self._estrategias = list(estrategias)

    @property
    def nombre(self):
        return f"{type(self).__name__}({self.columna})"

    def aprender(self, df):
        comparacion = None
        elegida = self._estrategias[0]
        if len(self._estrategias) > 1:
            comparacion = imp.comparar_estrategias(df.dropna(subset=[self.limite_superior]), self.columna,
                                                   self._estrategias, self.limite_superior)
            etiqueta = imp.elegir_estrategia(comparacion)
            elegida = next(e for e in self._estrategias if e.etiqueta == etiqueta)
        elegida.ajustar(df, self.columna)
        return {"estrategia": elegida, "metodo": elegida.etiqueta, "aprendido": elegida.parametros,
                "comparacion": comparacion}

    def aplicar(self, df):
        nulos = df[self.columna].isna()
        estimado = self._parametros["estrategia"].estimar(df, self.columna)
        df.loc[nulos, self.columna] = estimado[nulos]
        df[f"{self.columna}_IMPUTADO"] = nulos.astype(int)
        self._evidencia = {"metodo": self._parametros["metodo"], "imputados": int(nulos.sum())}
        return df


class ImputadorPuntoMedio(Transformador):
    """Imputa `columna` con (inferior + superior) / 2: garantiza inferior ≤ columna ≤ superior."""

    def __init__(self, columna, inferior, superior):
        super().__init__(columnas=[columna, inferior, superior])
        self.columna, self.inferior, self.superior = columna, inferior, superior

    @property
    def nombre(self):
        return f"{type(self).__name__}({self.columna})"

    def aprender(self, df):
        return {"regla": f"({self.inferior} + {self.superior}) / 2"}

    def aplicar(self, df):
        nulos = df[self.columna].isna()
        df.loc[nulos, self.columna] = ((df[self.inferior] + df[self.superior]) / 2)[nulos]
        df[f"{self.columna}_IMPUTADO"] = nulos.astype(int)
        self._evidencia = {"imputados": int(nulos.sum())}
        return df


# ============================================================ transformación (F2 sec. 4)
class DerivadorVariables(Transformador):
    """Desnivel, log10 de área y volumen, clase de tamaño, frente en agua, fuente agrupada y la
    macrozona como categoría con orden geográfico. Aprende qué fuentes son raras (< 1 %)."""

    CORTES_TAMANO = [0, 0.01, 0.1, 1, 10, np.inf]   # km², escala del dominio

    def __init__(self, umbral_raras=0.01):
        super().__init__(columnas=["AREA_KM2", "VOL_km3", "HMIN", "HMAX", "FRENTE_TER", "FUENTE_DIG", "MZON_GLAC"])
        self.umbral_raras = umbral_raras

    def aprender(self, df):
        return {"fuentes_raras": lim.categorias_raras(df["FUENTE_DIG"], self.umbral_raras),
                "cortes_tamano": self.CORTES_TAMANO, "orden_macrozona": utl.ORDEN_MACROZONA}

    def aplicar(self, df):
        if (df[["AREA_KM2", "VOL_km3"]] <= 0).any().any():
            raise ValueError("El logaritmo requiere AREA_KM2 y VOL_km3 positivos")
        df["RANGO_ALT"] = df["HMAX"] - df["HMIN"]
        df["LOG_AREA"] = np.log10(df["AREA_KM2"])
        df["LOG_VOL"] = np.log10(df["VOL_km3"])
        df["CLASE_TAMANO"] = pd.cut(df["AREA_KM2"], bins=self.CORTES_TAMANO, labels=utl.ETIQUETAS_TAMANO, right=False)
        df["FRENTE_AGUA"] = df["FRENTE_TER"].isin(["LAGO", "FIORDO"]).astype(int)
        df["FUENTE_GRUPO"] = lim.agrupar_categorias(df["FUENTE_DIG"], self._parametros["fuentes_raras"])
        df["MZON_GLAC"] = pd.Categorical(df["MZON_GLAC"], categories=utl.ORDEN_MACROZONA, ordered=True)
        self._evidencia = {"asimetria_log_area": round(float(df["LOG_AREA"].skew()), 2),
                           "asimetria_log_vol": round(float(df["LOG_VOL"].skew()), 2)}
        return df


class Redondeador(Transformador):
    """Redondea columnas calculadas para eliminar el ruido de punto flotante entre plataformas."""

    def __init__(self, columnas, decimales=12):
        super().__init__(columnas=columnas)
        self.decimales = decimales

    def aprender(self, df):
        return {"columnas": list(self._columnas), "decimales": self.decimales}

    def aplicar(self, df):
        df[list(self._columnas)] = df[list(self._columnas)].round(self.decimales)
        return df


class Categorizador(Transformador):
    """Declara como categoría las variables nominales (ahorra memoria y fija su rol)."""

    def aprender(self, df):
        return {"columnas": list(self._columnas)}

    def aplicar(self, df):
        for columna in self._columnas:
            df[columna] = df[columna].astype("category")
        return df


# ============================================================ codificación y escalamiento
class CodificadorOrdinal(Transformador):
    """Códigos 0..n−1 según un orden declarado (no alfabético), en la columna `salida`."""

    def __init__(self, columna, orden, salida):
        super().__init__(columnas=[columna])
        self.columna, self.orden, self.salida = columna, list(orden), salida

    @property
    def nombre(self):
        return f"{type(self).__name__}({self.columna})"

    def aprender(self, df):
        desconocidas = set(df[self.columna].dropna().astype(str)) - set(self.orden)
        if desconocidas:
            raise ValueError(f"{self.nombre}: categorías sin orden declarado: {sorted(desconocidas)}")
        return {"codigos": {c: i for i, c in enumerate(self.orden)}}

    def aplicar(self, df):
        df[self.salida] = lim.codificar_ordinal(df[self.columna], self.orden)
        return df


class CodificadorCiclico(Transformador):
    """Seno y coseno de la orientación: N (0°) y NW (315°) quedan vecinas; PLANO → (0, 0)."""

    def __init__(self, columna="ORIENTA"):
        super().__init__(columnas=[columna])
        self.columna = columna

    def aprender(self, df):
        return {"angulos": dict(lim.ANGULOS)}

    def aplicar(self, df):
        ciclicas = lim.codificar_orientacion(df[self.columna])
        df[ciclicas.columns] = ciclicas
        return df


class CodificadorOneHot(Transformador):
    """Una columna 0/1 por categoría. El vocabulario se aprende en `ajustar`: una categoría que
    aparezca solo al transformar no crea columnas nuevas."""

    def __init__(self, prefijos):
        super().__init__(columnas=list(prefijos))
        self.prefijos = dict(prefijos)

    def aprender(self, df):
        return {"categorias": {c: sorted(df[c].astype(str).unique()) for c in self.prefijos}}

    def aplicar(self, df):
        nuevas = {}
        for columna, prefijo in self.prefijos.items():
            texto = df[columna].astype(str)
            for categoria in self._parametros["categorias"][columna]:
                nuevas[f"{prefijo}_{categoria}"] = (texto == categoria).astype(int)
        self._evidencia = {"columnas_binarias": len(nuevas)}
        return pd.concat([df, pd.DataFrame(nuevas, index=df.index)], axis=1)


class EscaladorRobusto(Transformador):
    """(x − mediana) / RIC en columnas `<columna>_ESC`. Se eligió en F2 frente a StandardScaler y
    MinMaxScaler porque RANGO_ALT y HMEDIA conservan colas largas tras la transformación."""

    def __init__(self, columnas, decimales=12):
        super().__init__(columnas=columnas)
        self.decimales = decimales

    def aprender(self, df):
        if df[list(self._columnas)].isna().any().any():
            raise ValueError(f"{self.nombre}: no se puede escalar con valores nulos; imputar antes")
        escalador = RobustScaler().fit(df[list(self._columnas)])
        return {"centro": escalador.center_.tolist(), "escala": escalador.scale_.tolist()}

    def aplicar(self, df):
        for columna, centro, escala in zip(self._columnas, self._parametros["centro"], self._parametros["escala"]):
            df[f"{columna}_ESC"] = ((df[columna] - centro) / escala).round(self.decimales)
        return df


class SelectorColumnas(Transformador):
    """Deja solo las columnas indicadas, en ese orden (por ejemplo, la matriz del modelo)."""

    def aprender(self, df):
        return {"columnas": list(self._columnas)}

    def aplicar(self, df):
        return df[list(self._columnas)]
