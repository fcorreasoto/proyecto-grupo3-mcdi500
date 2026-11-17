"""Pipeline: encadena transformadores y avisa a sus observadores (patrón Observer).

`Pipeline` es composición: contiene transformadores y los ejecuta en orden sin heredar de ellos
ni conocer su tipo concreto. El bucle no tiene ninguna condición sobre el tipo de paso; esa
ausencia es la evidencia del polimorfismo, y es lo que permite agregar un paso nuevo sin
modificar esta clase.

Observer. En F2 cada decisión se registraba a mano en la bitácora después de calcularla, y la
cifra podía quedar desactualizada si cambiaba el código. Aquí el pipeline notifica a cada
observador suscrito al terminar un paso (nombre, filas, columnas, segundos, parámetros y
evidencia) sin saber quién escucha ni qué hace con el aviso. La bitácora se genera durante la
ejecución y no puede quedar desactualizada; medir tiempos o imprimir el avance son otros
observadores que se suscriben sin tocar el pipeline.
"""

import time

import pandas as pd

from transformadores import Transformador


class Pipeline:
    """Encadena transformadores y los ejecuta en orden."""

    def __init__(self, pasos=None, nombre="pipeline"):
        self.nombre = nombre
        self._pasos = []
        self._observadores = []
        self._ajustado = False
        for paso in pasos or []:
            self.agregar(paso)

    # ---------------------------------------------------------------------- composición
    def agregar(self, paso):
        if not isinstance(paso, Transformador):
            raise TypeError(f"Se esperaba un Transformador y se recibió {type(paso).__name__}")
        self._pasos.append(paso)
        self._ajustado = False
        return self

    def suscribir(self, observador):
        if not callable(getattr(observador, "notificar", None)):
            raise TypeError(f"{type(observador).__name__} no tiene un método notificar()")
        self._observadores.append(observador)
        return self

    @property
    def pasos(self):
        return tuple(self._pasos)          # tupla: no se puede alterar el orden desde fuera

    @property
    def ajustado(self):
        return self._ajustado

    # ------------------------------------------------------------------------ ejecución
    def ajustar_transformar(self, df):
        """Ajusta cada paso con la salida del anterior y devuelve el resultado final (una pasada)."""
        if not self._pasos:
            raise RuntimeError(f"{self.nombre}: no tiene pasos")
        resultado = df
        for paso in self._pasos:                                   # polimorfismo
            inicio = time.perf_counter()
            resultado = paso.ajustar(resultado).transformar(resultado)
            self._notificar(paso, resultado, time.perf_counter() - inicio, "ajustar_transformar")
        self._ajustado = True
        return resultado

    def ajustar(self, df):
        """Aprende los parámetros de cada paso con `df`."""
        self.ajustar_transformar(df)
        return self

    def transformar(self, df):
        """Aplica los pasos ya ajustados a cualquier conjunto con las mismas columnas."""
        if not self._ajustado:
            raise RuntimeError(f"{self.nombre}: hay que ajustar antes de transformar")
        resultado = df
        for paso in self._pasos:
            inicio = time.perf_counter()
            resultado = paso.transformar(resultado)
            self._notificar(paso, resultado, time.perf_counter() - inicio, "transformar")
        return resultado

    def _notificar(self, paso, resultado, segundos, fase):
        evento = {"pipeline": self.nombre, "fase": fase, "paso": paso.nombre, "filas": resultado.shape[0],
                  "columnas": resultado.shape[1], "segundos": segundos,
                  "parametros": paso.parametros, "evidencia": paso.evidencia}
        for observador in self._observadores:
            observador.notificar(evento)

    # ---------------------------------------------------------------------- inspección
    def resumen(self):
        return pd.DataFrame([{"orden": i, "paso": p.nombre, "clase": type(p).__name__,
                              "clase_base": type(p).__mro__[1].__name__}
                             for i, p in enumerate(self._pasos, start=1)])

    def __getitem__(self, nombre):
        for paso in self._pasos:
            if paso.nombre == nombre:
                return paso
        raise KeyError(f"{self.nombre}: no hay un paso llamado {nombre!r}")

    def __len__(self):
        return len(self._pasos)

    def __repr__(self):
        estado = "ajustado" if self._ajustado else "sin ajustar"
        return f"Pipeline({self.nombre!r}, {len(self._pasos)} pasos, {estado})"


# ============================================================================ observadores
class RegistroEjecucion:
    """Observador que acumula un evento por paso y los entrega como tabla."""

    def __init__(self):
        self._eventos = []

    def notificar(self, evento):
        self._eventos.append(evento)

    def tabla(self, columnas=("pipeline", "paso", "filas", "columnas", "segundos")):
        return pd.DataFrame(self._eventos, columns=list(columnas))

    def __len__(self):
        return len(self._eventos)


class ReporteConsola:
    """Observador que imprime el avance mientras ocurre."""

    def notificar(self, evento):
        print(f"  {evento['pipeline']:<10} {evento['paso']:<36} {evento['filas']:>6} filas × "
              f"{evento['columnas']:>3} col  [{evento['segundos']:.3f} s]")


class ObservadorBitacora:
    """Observador que escribe en la `utilidades.Bitacora` del proyecto la evidencia de cada paso.

    Solo registra los pasos que dejan evidencia; `textos` permite asociar a cada paso la decisión
    que lo justifica (la misma redacción de la bitácora de F2).
    """

    def __init__(self, bitacora, textos=None):
        self.bitacora = bitacora
        self.textos = textos or {}

    def notificar(self, evento):
        if not evento["evidencia"]:
            return
        decision = self.textos.get(evento["paso"], evento["paso"])
        evidencia = "; ".join(f"{k} = {v}" for k, v in evento["evidencia"].items())
        self.bitacora.registrar(evento["pipeline"], decision, evidencia)
