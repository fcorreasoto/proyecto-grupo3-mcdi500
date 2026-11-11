"""Utilidades compartidas del proyecto MCDI500 · Grupo 3.

Inventario Público de Glaciares de Chile 2022. Este módulo reúne lo que usan varias
fases (rutas, integridad del dato, entorno, trazabilidad y bitácora), para que cada
función se escriba y se pruebe una sola vez. F1 lo importa y lo prueba (sección 4.1) y F2 lo
reutiliza; las fases siguientes lo importarán del mismo modo.
"""

import hashlib
import re
import subprocess
from pathlib import Path

import pandas as pd

SEMILLA = 42  # declarada para cualquier proceso aleatorio de las fases siguientes
ARCHIVO_INVENTARIO = "Inventario_Publico_de_Glaciares_2022.csv"
HUELLA_INVENTARIO = "5691de5d7d7ffe2c8586a7066e227ac5cc91fa1ec69f54096e937a054c283f1d"


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
