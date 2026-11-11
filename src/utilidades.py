"""Utilidades compartidas del proyecto MCDI500 · Grupo 3.

Inventario Público de Glaciares de Chile 2022. Este módulo reúne lo que usan varias fases
(rutas, integridad del dato, carga de los datos procesados, entorno, trazabilidad, pruebas y
bitácora), para que cada función se escriba y se pruebe una sola vez. F1 lo importa y lo prueba
(sección 4.1) y F2 lo reutiliza; las fases siguientes lo importarán del mismo modo.
"""

import contextlib
import hashlib
import io
import re
import subprocess
from pathlib import Path

import pandas as pd

SEMILLA = 42  # declarada para cualquier proceso aleatorio de las fases siguientes
ARCHIVO_INVENTARIO = "Inventario_Publico_de_Glaciares_2022.csv"
HUELLA_INVENTARIO = "5691de5d7d7ffe2c8586a7066e227ac5cc91fa1ec69f54096e937a054c283f1d"

# Tipos que F2 declara y que un CSV no conserva: cargar_limpio() los restaura al releer.
ORDEN_MACROZONA = ["MACROZONA NORTE", "MACROZONA CENTRO", "MACROZONA SUR", "MACROZONA AUSTRAL"]
ETIQUETAS_TAMANO = ["< 0,01", "0,01–0,1", "0,1–1", "1–10", "> 10"]          # clases de AREA_KM2 (km²)
ORDINALES_LIMPIO = {"MZON_GLAC": ORDEN_MACROZONA, "CLASE_TAMANO": ETIQUETAS_TAMANO}
COLUMNAS_CODIGO = ["COD_CUEN", "COD_SCUEN", "COD_SSCUEN", "CUT_REG", "CUT_PROV", "CUT_COM", "WGI_2", "WGI_3"]
NOMINALES_LIMPIO = ["CLASIFICA", "REGION", "FRENTE_TER", "FUENTE_GRUPO"]


class ProyectoError(Exception):
    """Error propio del proyecto: distingue «los datos o el repositorio no son los
    esperados» de los errores de pandas, NumPy o scikit-learn."""


# --------------------------------------------------------------------------- rutas
def localizar_raiz(inicio=None, archivo=ARCHIVO_INVENTARIO):
    """Sube desde `inicio` (o el directorio actual) hasta la carpeta que contiene data/raw/<archivo>.

    Funciona aunque Jupyter abra el kernel en F1/, F2/ o en la raíz del repositorio.

    Lanza
    -----
    FileNotFoundError
        Si ninguna carpeta superior contiene el archivo de datos.
    """
    inicio = Path.cwd() if inicio is None else Path(inicio)
    for carpeta in (inicio, *inicio.parents):
        if (carpeta / "data" / "raw" / archivo).is_file():
            return carpeta
    raise FileNotFoundError(
        f"No se encontró data/raw/{archivo} desde {inicio}. "
        "Abra el notebook desde la carpeta del repositorio clonado."
    )


# --------------------------------------------------------------- integridad del dato
def huella_sha256(ruta, bloque=1024 * 1024):
    """Huella SHA-256 de un archivo, leído por bloques para no cargarlo entero en memoria."""
    h = hashlib.sha256()
    with open(ruta, "rb") as archivo:
        for trozo in iter(lambda: archivo.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def verificar_huella(ruta, esperada=HUELLA_INVENTARIO):
    """Devuelve la huella del archivo; lanza ProyectoError si no coincide con la esperada."""
    huella = huella_sha256(ruta)
    if huella != esperada:
        raise ProyectoError(
            f"{Path(ruta).name} no coincide con la versión registrada "
            f"(SHA-256 {huella[:12]}… ≠ {esperada[:12]}…). Restaurar con: git checkout -- data/raw/"
        )
    return huella


def cargar_inventario(ruta):
    """Lee el CSV original sin alterar valores; `utf-8-sig` ignora una posible marca BOM."""
    return pd.read_csv(ruta, encoding="utf-8-sig", low_memory=False)


def cargar_limpio(ruta):
    """Lee data/processed/glaciares_limpio.csv restaurando los tipos que el CSV no conserva.

    - Ordinales (`MZON_GLAC`, `CLASE_TAMANO`) como categorías con el orden declarado, no alfabético.
    - Códigos (`COD_*`, `CUT_*`, `WGI_*`) e identificador como texto, no como enteros.
    - `FUEN_FECHA` como fecha, `FUEN_ANIO` como entero con nulos y nominales como categoría.

    Lanza
    -----
    ProyectoError
        Si una ordinal contiene una categoría sin orden declarado.
    """
    tipos = {columna: "string" for columna in ["COD_GLA", *COLUMNAS_CODIGO]}
    df = pd.read_csv(ruta, dtype=tipos, low_memory=False)
    if "FUEN_FECHA" in df:
        df["FUEN_FECHA"] = pd.to_datetime(df["FUEN_FECHA"], format="%Y-%m-%d", errors="coerce")
    if "FUEN_ANIO" in df:
        df["FUEN_ANIO"] = df["FUEN_ANIO"].astype("Int64")
    for columna, orden in ORDINALES_LIMPIO.items():
        if columna in df:
            desconocidas = set(df[columna].dropna()) - set(orden)
            if desconocidas:
                raise ProyectoError(f"{columna} tiene categorías sin orden declarado: {sorted(desconocidas)}")
            df[columna] = pd.Categorical(df[columna], categories=orden, ordered=True)
    for columna in NOMINALES_LIMPIO:
        if columna in df:
            df[columna] = df[columna].astype("category")
    return df


# ------------------------------------------------------------------------- entorno
def leer_requirements(ruta):
    """Devuelve {paquete en minúsculas: versión} a partir de las líneas 'paquete==versión'."""
    declaradas = {}
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "==" in linea:
            nombre, version = linea.split("==", 1)
            declaradas[nombre.strip().lower()] = version.strip()
    return declaradas


# -------------------------------------------------------------------- trazabilidad
def _git(raiz, *argumentos):
    return subprocess.run(["git", *argumentos], cwd=raiz, capture_output=True,
                          text=True, check=True, timeout=20).stdout.strip()


def version_repositorio(raiz, excluir=()):
    """Rama, commit y si hay cambios sin commitear (ignorando las rutas en `excluir`,
    que son las salidas que el propio notebook regenera). No falla si Git no está disponible."""
    try:
        exclusiones = [f":!{ruta}" for ruta in excluir]
        return {
            "rama": _git(raiz, "rev-parse", "--abbrev-ref", "HEAD"),
            "commit": _git(raiz, "rev-parse", "--short", "HEAD"),
            "cambios_sin_commit": bool(_git(raiz, "status", "--porcelain", "--", ".", *exclusiones)),
        }
    except (OSError, subprocess.SubprocessError):
        return {"rama": "no disponible", "commit": "no disponible", "cambios_sin_commit": None}


def email_valido(email):
    """True si el email tiene forma usuario@dominio.tld y no es un nombre de equipo local
    (p. ej. usuario@MacBook.local), que GitHub no puede asociar a ninguna cuenta."""
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", email or "")) and not email.lower().endswith(".local")


def identidad_git(raiz):
    """Nombre y email que Git usará en los commits de este repositorio, y si el email es válido."""
    try:
        nombre = _git(raiz, "config", "user.name")
        email = _git(raiz, "config", "user.email")
    except (OSError, subprocess.SubprocessError):
        return {"user.name": None, "user.email": None, "email_valido": False}
    return {"user.name": nombre, "user.email": email, "email_valido": email_valido(email)}


# ------------------------------------------------------------------------- pruebas
def espera_error(tipo_error, funcion, *args, **kwargs):
    """Pasa si `funcion` lanza `tipo_error`; lanza AssertionError si no lanza nada."""
    try:
        funcion(*args, **kwargs)
    except tipo_error:
        return
    raise AssertionError(f"Se esperaba {tipo_error.__name__}")


def prueba(condicion, mensaje="resultado inesperado"):
    """Aserción con mensaje, utilizable dentro de una lambda."""
    assert condicion, mensaje


def ejecutar_pruebas(pruebas):
    """Ejecuta (tipo, nombre, función) y devuelve una tabla OK / FALLA sin detenerse en la primera.

    Silencia lo que impriman las funciones probadas (por ejemplo, los registros de la bitácora).
    """
    filas = []
    for tipo, nombre, funcion in pruebas:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                funcion()
            resultado = "OK"
        except AssertionError as error:
            resultado = f"FALLA: {error}"
        filas.append({"tipo": tipo, "prueba": nombre, "resultado": resultado})
    return pd.DataFrame(filas, columns=["tipo", "prueba", "resultado"])


# ------------------------------------------------------------------------ bitácora
class Bitacora:
    """Registro ordenado de decisiones, cada una con su evidencia cuantitativa.

    Re-ejecutar la celda que registra una decisión actualiza su evidencia en vez de duplicarla.
    """

    def __init__(self, fase):
        self.fase = fase
        self._registros = []

    def registrar(self, etapa, decision, evidencia):
        if not str(evidencia).strip():
            raise ValueError("Toda decisión debe registrarse con su evidencia")
        for registro in self._registros:
            if (registro["etapa"], registro["decision"]) == (etapa, decision):
                registro["evidencia"] = evidencia
                break
        else:
            self._registros.append({"n": len(self._registros) + 1, "etapa": etapa,
                                    "decision": decision, "evidencia": evidencia})
        print(f"[{self.fase} · {etapa}] {decision} — {evidencia}")

    def tabla(self):
        return pd.DataFrame(self._registros, columns=["n", "etapa", "decision", "evidencia"])

    def exportar_markdown(self, ruta):
        filas = ["| # | Etapa | Decisión | Evidencia |", "|---|---|---|---|"]
        filas += [f"| {r['n']} | {r['etapa']} | {r['decision']} | {r['evidencia']} |" for r in self._registros]
        Path(ruta).write_text(f"# Bitácora de decisiones · {self.fase}\n\n" + "\n".join(filas) + "\n",
                              encoding="utf-8")

    def __len__(self):
        return len(self._registros)
