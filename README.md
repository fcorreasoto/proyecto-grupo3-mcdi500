# MCDI500 · Grupo 3 — Análisis reproducible del Inventario Público de Glaciares de Chile 2022

Proyecto del curso **MCDI500 Programación para la Ciencia de Datos**, Magíster en Ciencia de Datos e Inteligencia Artificial, Universidad Andrés Bello. Docente: Dr. Omar Salinas Silva.

**Integrantes:** Aníbal Reyes · Francisco Correa Soto · Gustavo Aloy · Roberto Gaubert

| Fase | Estado | Producto |
|---|---|---|
| F1 · Definición y entorno | ✔ Implementada | [`F1/F1_Definicion.ipynb`](F1/F1_Definicion.ipynb) |
| F2 · Obtención, limpieza, transformación y validación | ✔ Implementada | [`F2/F2_Procesamiento.ipynb`](F2/F2_Procesamiento.ipynb) |
| F3 · Análisis | ○ Proyectada (semana 2) | — |
| F4 · Comunicación | ○ Proyectada (semana 3) | — |

Informe técnico de la Sumativa 1: [`docs/informe/mcdi500_sumativa1_grupo3.pdf`](docs/informe/mcdi500_sumativa1_grupo3.pdf)

## Problemática

Los glaciares son reservas hídricas estratégicas para Chile. La DGA publica un inventario oficial de 26.180 glaciares, pero su CSV no es directamente analizable: tiene columnas vacías, coordenadas leídas como texto por usar coma decimal, fechas en formatos mixtos y magnitudes muy asimétricas. El proyecto busca caracterizar la distribución de los glaciares con un procedimiento transparente y reproducible.

**Pregunta de investigación:** ¿Cómo se distribuyen los glaciares del Inventario Público de Glaciares 2022 según región, clasificación, superficie y volumen estimado?

**Objetivo general:** Caracterizar la distribución territorial y las propiedades físicas de los glaciares registrados en el inventario mediante un flujo de análisis reproducible en Python.

**Objetivos específicos**
1. Verificar la estructura, la calidad y el rol analítico de las 45 variables del inventario (F1–F2).
2. Documentar y ejecutar la limpieza y transformación sin modificar el archivo original (F2).
3. Resumir número de glaciares, superficie y volumen estimado por región y clasificación (F3).
4. Generar tablas y visualizaciones reproducibles desde el repositorio (F4).

**Fuera del alcance:** tendencias temporales de pérdida de hielo (el inventario es transversal), modelos predictivos y cruce con datos climáticos externos.

## Datos

| | |
|---|---|
| Fuente | Dirección General de Aguas (DGA), *Inventario Público de Glaciares de Chile 2022*. Uso académico citando la fuente |
| Archivo original | `data/raw/Inventario_Publico_de_Glaciares_2022.csv` (26.180 filas × 45 columnas, 9,46 MB) |
| Huella SHA-256 | `5691de5d7d7ffe2c8586a7066e227ac5cc91fa1ec69f54096e937a054c283f1d` |
| Archivo procesado (F2) | `data/processed/inventario_glaciares_2022_procesado.csv` (26.180 × 48) |
| Perfil de calidad | [`docs/validacion_dataset.md`](docs/validacion_dataset.md) y `data/processed/perfil_f2.csv` |

El archivo de `data/raw/` **nunca se modifica**. F2 recalcula su huella SHA-256 y falla si el archivo cambió.

## Estructura del repositorio

```text
proyecto-grupo3-mcdi500/
├── F1/
│   └── F1_Definicion.ipynb          # Problema, objetivos, entorno y reconocimiento del inventario
├── F2/
│   └── F2_Procesamiento.ipynb       # Obtención → exploración → limpieza → transformación → validación
├── data/
│   ├── raw/                         # CSV original de la DGA (inmutable)
│   └── processed/                   # Salidas de F2 (se generan al ejecutar el notebook)
├── docs/
│   ├── validacion_dataset.md        # Perfil de las 45 variables y requisitos del curso
│   ├── f1/                          # Mapa conceptual de la Formativa 1 (.drawio y .pdf)
│   └── informe/                     # Informe técnico de la Sumativa 1 (.docx y .pdf)
├── requirements.txt                 # Dependencias con versión exacta (pip freeze)
├── .gitignore
└── README.md
```

## Entorno y dependencias

- **Python:** 3.12 o superior. El proyecto se probó con Python 3.12.3 y 3.14.6.
- **Librerías principales:** pandas 3.1.1, NumPy 2.5.4, JupyterLab 4.6.6 e ipykernel 7.4.0. Matplotlib 3.11.2, seaborn 0.13.2 y scikit-learn 1.9.1 quedan instaladas para F3–F4.
- La lista completa con versiones exactas está en [`requirements.txt`](requirements.txt).

### Instalación

```bash
git clone https://github.com/fcorreasoto/proyecto-grupo3-mcdi500.git
cd proyecto-grupo3-mcdi500
```

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Luego, en cualquier sistema:
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Ejecución de los notebooks

Ejecútalos **en orden** con el kernel del entorno virtual (`.venv`). En JupyterLab usa *Kernel → Restart Kernel and Run All Cells*.

```bash
jupyter lab
```

1. **`F1/F1_Definicion.ipynb`**
   - Presenta el problema, la pregunta, los objetivos, el alcance, las restricciones y los supuestos.
   - Verifica las versiones del entorno, localiza el CSV con rutas relativas y construye el diccionario de las 45 variables.
   - **No modifica ni exporta datos.**
   - Resultado esperado: «Verificación F1 superada».
2. **`F2/F2_Procesamiento.ipynb`**
   - Carga el CSV, registra su huella SHA-256 y diagnostica faltantes, duplicados, atípicos y fechas.
   - Crea `LATITUD_NUM`, `LONGITUD_NUM` y `FUEN_FECHA_DT` sobre una copia del inventario y valida el resultado con `assert`.
   - Exporta los archivos a `data/processed/`.
   - Resultado esperado: «Pruebas superadas…» y «Dimensiones exportadas: (26180, 48)».

También pueden ejecutarse sin abrir JupyterLab:

```bash
jupyter nbconvert --to notebook --execute --inplace F1/F1_Definicion.ipynb
jupyter nbconvert --to notebook --execute --inplace F2/F2_Procesamiento.ipynb
```

Los notebooks pueden ejecutarse desde su propia carpeta o desde la raíz del repositorio. No requieren internet ni semilla aleatoria, porque el pipeline es determinista.

## Decisiones principales de la Fase 2

| Hallazgo | Decisión |
|---|---|
| `CUBIERTO` y `OBSERVACIO` 100 % vacías | Se conservan en el archivo y se excluyen de los análisis. No hay valores desde los cuales imputar |
| `CH_CASQ` 97,24 % faltante | Se conserva sin imputar, porque la fuente no documenta el significado del faltante |
| `LATITUD` y `LONGITUD` como texto con coma decimal | Se crean columnas `float` auxiliares. Las 26.180 se convierten sin fallas |
| `FUEN_FECHA` con formatos mixtos | Se crea `FUEN_FECHA_DT` (DD/MM/AAAA). Las 13 no interpretables quedan como `NaT` y se reportan |
| Superficie y volumen muy asimétricos | No se eliminan atípicos, porque son glaciares reales |
| Variables de análisis sin faltantes | No se imputa nada. Ningún registro se elimina |

El detalle y la justificación de cada decisión están en el notebook F2 (§3 y §8) y en el informe (sección 4.2).

## Control de versiones

- Los commits usan prefijos por tipo de cambio: `docs:`, `data:`, `feat:`, `fix:`.
- Cada integrante hace commits desde su propia cuenta.
- Desde la Fase 3, cada tarea se desarrolla en una rama propia y se integra a `main` mediante Pull Request.
- No se versionan `.venv/`, las cachés de Python, `.env` ni la carpeta `material/` con el material de clase.
- Los notebooks se versionan **con sus salidas**, que sirven como evidencia de ejecución.

## Criterios de reproducibilidad

- No modificar los archivos de `data/raw/`.
- Usar rutas relativas y declarar las versiones de las dependencias.
- Ejecutar los notebooks de principio a fin con el kernel del entorno virtual antes de cada entrega.
- Antes de entregar, otro integrante clona el repositorio, reconstruye el entorno y ejecuta ambos notebooks.
