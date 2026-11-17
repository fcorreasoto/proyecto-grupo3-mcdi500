"""Aplanado de los metadatos del pipeline (recursividad).

Los metadatos de cada fase son un diccionario anidado de profundidad variable (proyecto → datos
→ fuente → ..., decisiones → imputación → HMIN → método). Para guardarlos en un CSV de dos
columnas (clave, valor) hay que recorrerlos completos sin saber de antemano cuántos niveles
tienen: ese es el caso en que la recursión se justifica, porque cada subdiccionario se trata
igual que el diccionario completo.

`aplanar` es la versión recursiva de F2 (sección 7), trasladada sin cambios. `aplanar_iterativo`
hace lo mismo con una pila explícita; medicion.py compara ambas en tiempo, memoria y en el
límite de profundidad de Python (sys.getrecursionlimit()).
"""


def aplanar(estructura, prefijo="", separador="."):
    """Aplana un diccionario anidado en uno de un solo nivel con claves 'a.b.c' (recursiva).

    >>> aplanar({"a": {"b": 1, "c": {"d": 2}}})
    {'a.b': 1, 'a.c.d': 2}
    """
    if not isinstance(estructura, dict):
        raise TypeError(f"Se esperaba un diccionario y se recibió {type(estructura).__name__}")
    plano = {}
    for clave, valor in estructura.items():
        ruta = f"{prefijo}{separador}{clave}" if prefijo else str(clave)
        if isinstance(valor, dict):
            plano.update(aplanar(valor, ruta, separador))        # caso recursivo
        elif isinstance(valor, (list, tuple)):
            plano[ruta] = ", ".join(map(str, valor))             # caso base: lista → texto
        else:
            plano[ruta] = valor                                  # caso base: valor simple
    return plano


def aplanar_iterativo(estructura, separador="."):
    """Mismo resultado que `aplanar`, con una pila explícita en lugar de llamadas recursivas.

    Recorre en el mismo orden (profundidad primero, claves en orden de inserción) para que
    ambas versiones produzcan diccionarios idénticos, incluido el orden de las claves.
    """
    if not isinstance(estructura, dict):
        raise TypeError(f"Se esperaba un diccionario y se recibió {type(estructura).__name__}")
    plano = {}
    pila = [("", iter(estructura.items()))]                      # (prefijo, elementos pendientes)
    while pila:
        prefijo, pendientes = pila[-1]
        siguiente = next(pendientes, None)
        if siguiente is None:                                    # nivel terminado: volver al anterior
            pila.pop()
            continue
        clave, valor = siguiente
        ruta = f"{prefijo}{separador}{clave}" if prefijo else str(clave)
        if isinstance(valor, dict):
            pila.append((ruta, iter(valor.items())))             # bajar un nivel
        elif isinstance(valor, (list, tuple)):
            plano[ruta] = ", ".join(map(str, valor))
        else:
            plano[ruta] = valor
    return plano


def profundidad(estructura):
    """Niveles de anidamiento de un diccionario (recursiva)."""
    if not isinstance(estructura, dict) or not estructura:
        return 0
    return 1 + max(profundidad(v) for v in estructura.values())


def anidar(niveles, hojas=1):
    """Diccionario de prueba con `niveles` de profundidad y `hojas` valores por nivel."""
    estructura = {f"v{i}": i for i in range(hojas)}
    for nivel in range(niveles - 1, 0, -1):
        estructura = {f"n{nivel}": estructura, **{f"v{i}": i for i in range(hojas)}}
    return estructura
