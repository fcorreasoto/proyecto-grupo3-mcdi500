"""Estrategias de imputación intercambiables (patrón Strategy).

Problema que resuelve: en F2 se compararon cuatro formas de imputar HMIN (media, mediana,
mediana por comuna y HMEDIA menos el desnivel mediano por comuna). Cada una era una rama de un
`if` dentro de `imputar()`, así que agregar una quinta obligaba a modificar esa función y la que
las comparaba. Aquí cada forma es una clase con la misma interfaz (`ajustar` y `estimar`), y
`ImputadorEstrategia` (transformadores.py) recibe la estrategia como parámetro: agregar una
nueva no modifica ninguna clase existente (principio de abierto y cerrado).

Cada estrategia separa lo que aprende (`ajustar`) de lo que aplica (`estimar`), igual que los
transformadores: lo aprendido queda en atributos internos y solo se lee mediante `parametros`.
"""

import pandas as pd

import utilidades as utl


class EstrategiaImputacion:
    """Contrato común: aprender un valor de reemplazo y estimarlo para cada fila."""

    etiqueta = "sin definir"

    def __init__(self):
        self._parametros = {}
        self._ajustada = False

    @property
    def parametros(self):
        return dict(self._parametros)                       # copia defensiva

    def ajustar(self, df, columna):
        if columna not in df.columns:
            raise KeyError(f"{self.etiqueta}: la columna {columna} no existe")
        self._parametros = self._aprender(df, columna)
        self._ajustada = True
        return self

    def estimar(self, df, columna):
        """Serie con el valor estimado para cada fila de `df` (se usa solo donde hay nulos)."""
        if not self._ajustada:
            raise RuntimeError(f"{self.etiqueta}: hay que ajustar antes de estimar")
        return self._estimar(df, columna)

    def _aprender(self, df, columna):
        raise NotImplementedError("Cada estrategia debe implementar _aprender()")

    def _estimar(self, df, columna):
        raise NotImplementedError("Cada estrategia debe implementar _estimar()")

    def __repr__(self):
        return f"{type(self).__name__}()"


class PorMedia(EstrategiaImputacion):
    etiqueta = "media global"

    def _aprender(self, df, columna):
        return {"valor": df[columna].mean()}

    def _estimar(self, df, columna):
        return pd.Series(self._parametros["valor"], index=df.index)


class PorMediana(EstrategiaImputacion):
    etiqueta = "mediana global"

    def _aprender(self, df, columna):
        return {"valor": df[columna].median()}

    def _estimar(self, df, columna):
        return pd.Series(self._parametros["valor"], index=df.index)


class PorMedianaGrupo(EstrategiaImputacion):
    """Mediana de cada grupo; los grupos sin datos usan la mediana global."""

    def __init__(self, grupo):
        super().__init__()
        self.grupo = grupo

    @property
    def etiqueta(self):
        return f"mediana por {self.grupo.lower()}"

    def _aprender(self, df, columna):
        return {"por_grupo": df.groupby(self.grupo)[columna].median().to_dict(),
                "global": df[columna].median()}

    def _estimar(self, df, columna):
        return df[self.grupo].map(self._parametros["por_grupo"]).astype(float).fillna(self._parametros["global"])

    def __repr__(self):
        return f"{type(self).__name__}({self.grupo!r})"


class PorDiferenciaGrupo(EstrategiaImputacion):
    """`referencia` menos la diferencia mediana (referencia − columna) del grupo, con piso `minimo`.

    Para HMIN: HMEDIA − desnivel mediano por comuna. Respeta HMIN ≤ HMEDIA por construcción
    siempre que el desnivel mediano sea positivo.
    """

    def __init__(self, grupo, referencia, minimo=0.0):
        super().__init__()
        self.grupo = grupo
        self.referencia = referencia
        self.minimo = minimo

    @property
    def etiqueta(self):
        return f"{self.referencia} − desnivel mediano por {self.grupo.lower()}"

    def _aprender(self, df, columna):
        diferencia = df[self.referencia] - df[columna]
        return {"por_grupo": diferencia.groupby(df[self.grupo]).median().to_dict(),
                "global": diferencia.median()}

    def _estimar(self, df, columna):
        diferencia = df[self.grupo].map(self._parametros["por_grupo"]).astype(float).fillna(self._parametros["global"])
        return (df[self.referencia] - diferencia).clip(lower=self.minimo)

    def __repr__(self):
        return f"{type(self).__name__}({self.grupo!r}, {self.referencia!r})"


# --------------------------------------------------------------- comparación y elección
def imputar_con(df, columna, estrategia):
    """Ajusta la estrategia en `df`, rellena los nulos de `columna` y agrega la bandera <columna>_IMPUTADO."""
    df = df.copy()
    nulos = df[columna].isna()
    estimado = estrategia.ajustar(df, columna).estimar(df, columna)
    df.loc[nulos, columna] = estimado[nulos]
    df[f"{columna}_IMPUTADO"] = nulos.astype(int)
    return df


def comparar_estrategias(df, columna, estrategias, limite_superior):
    """Compara eliminar filas con cada estrategia: dispersión, violaciones físicas y área perdida.

    `limite_superior` es la columna que no se debe superar (para HMIN, HMEDIA).
    """
    desv_observada = df[columna].std()
    nulos = df[columna].isna()
    sin_nulos = df[~nulos]
    filas = [{"metodo": "eliminar filas", "filas": len(sin_nulos), "desv_est": sin_nulos[columna].std(),
              "violaciones": 0, "area_perdida_km2": df.loc[nulos, "AREA_KM2"].sum()}]
    for estrategia in estrategias:                           # polimorfismo: misma llamada para todas
        r = imputar_con(df, columna, estrategia)
        filas.append({"metodo": estrategia.etiqueta, "filas": len(r), "desv_est": r[columna].std(),
                      "violaciones": int((r.loc[nulos, columna] > r.loc[nulos, limite_superior]).sum()),
                      "area_perdida_km2": 0.0})
    tabla = pd.DataFrame(filas)
    tabla["cambio_desv_pct"] = 100 * (tabla["desv_est"] / desv_observada - 1)
    return tabla.round({"desv_est": 2, "cambio_desv_pct": 4, "area_perdida_km2": 2})


def elegir_estrategia(tabla):
    """Regla declarada en F2: sin pérdida de filas, sin violaciones físicas y menor |cambio de desviación|.

    A diferencia de F2, exige explícitamente que no se pierdan filas: `area_perdida_km2` está
    redondeada a 2 decimales y con glaciares muy pequeños podría valer 0 aunque se eliminen
    filas. Con el inventario el método elegido es el mismo.
    """
    candidatos = tabla[(tabla["filas"] == tabla["filas"].max()) & (tabla["area_perdida_km2"] == 0)
                       & (tabla["violaciones"] == 0)]
    if candidatos.empty:
        raise utl.ProyectoError("Ninguna estrategia de imputación cumple la regla declarada")
    return candidatos.loc[candidatos["cambio_desv_pct"].abs().idxmin(), "metodo"]


def estrategias_hmin():
    """Las cuatro estrategias que F2 comparó para HMIN, en el mismo orden."""
    return [PorMedia(), PorMediana(), PorMedianaGrupo("COMUNA"), PorDiferenciaGrupo("COMUNA", "HMEDIA")]
