# MCDI500 · Grupo 3 — Análisis reproducible del Inventario Público de Glaciares de Chile 2022

Proyecto del curso **MCDI500 Programación para la Ciencia de Datos**, Magíster en Ciencia de Datos e Inteligencia Artificial, Universidad Andrés Bello. Docente: Dr. Omar Salinas Silva.

**Integrantes:** Francisco Correa Soto · Gustavo Aloy Angella · Roberto Gaubert Urbina

| Fase | Estado | Producto |
|---|---|---|
| F1 · Definición y entorno | ✔ Implementada | [`F1/F1_Definicion.ipynb`](F1/F1_Definicion.ipynb) |
| F2 · Obtención, limpieza, transformación y validación | ✔ Implementada | [`F2/F2_Procesamiento.ipynb`](F2/F2_Procesamiento.ipynb) |
| F3 · Núcleo algorítmico | ◐ En desarrollo (semana 2) | Pipeline POO en `src/` ✔ · `src/concentracion.py` · `src/medicion.py` · `F3/` |
| F4 · Comunicación | ○ Proyectada (semana 3) | — |

Informe técnico de la Sumativa 1: [`docs/informe/mcdi500_sumativa1_grupo3.pdf`](docs/informe/mcdi500_sumativa1_grupo3.pdf)

## Problemática

Los glaciares son reservas hídricas estratégicas para Chile. La DGA publica el inventario oficial (26.180 glaciares, 45 variables) y sus totales, pero no un cálculo reproducible de **cuán concentrada está la superficie glaciar**. Además, su CSV no es directamente analizable: tiene columnas vacías, coordenadas leídas como texto, fechas en formatos mixtos y faltantes encubiertos. **Nuestro aporte** es medir esa concentración con un procedimiento reproducible de punta a punta: dato verificado, pipeline versionado y probado.

**Pregunta de investigación:** ¿Qué tan concentrada está la superficie glaciar en pocos glaciares y regiones, y cambia esa concentración según la clasificación del glaciar? La exploración la sustenta: el 1 % de los glaciares reúne el 71,5 % de la superficie, y Magallanes y Aysén el 91,1 % (F2, sección 2.2.1). El volumen no se trata como un hallazgo independiente: se estimó desde el área, y su concentración (93,8 % en el 1 % mayor) es una consecuencia de la de la superficie.

**Objetivo general:** Medir, mediante un flujo reproducible en Python, cuán concentrada está la superficie de los glaciares de Chile en pocos glaciares y regiones, y cómo varía esa concentración según la clasificación del glaciar, explicando la del volumen como magnitud derivada del área.

**Objetivos específicos**
1. Verificar la estructura, la calidad y el rol analítico de las 45 variables, y que el volumen se estimó desde el área (F1–F2).
2. Documentar y ejecutar la limpieza y transformación sin modificar el archivo original (F2).
3. Construir el núcleo algorítmico (F3): reorganizar el pipeline en componentes reutilizables con medición de eficiencia y sin alterar ningún resultado, y calcular dentro de ese diseño la concentración de la superficie (participación del 1 % y del 10 % mayores, curva de Lorenz y Gini, por región y por clasificación) y la del volumen como derivada.
4. Comunicar con tablas y visualizaciones reproducibles si la concentración cambia según la clasificación (F4).

**Supuesto clave (verificado en F2 sección 2.3):** el espesor y el volumen **no son mediciones**. Se estimaron desde el área con la fórmula de Chen y Ohmura (1990), `ESP_MED = 28,5 · AREA^0,357` (R² ≥ 0,998 en los cinco tipos), de modo que `VOL ≈ 0,0285 · AREA^1,357` (× 0,6 en glaciares rocosos). Por eso la superficie es la magnitud principal y el volumen una magnitud derivada: como el exponente 1,357 es mayor que 1, los glaciares grandes pesan más en volumen que en área y la concentración del volumen amplifica la de la superficie (Gini 0,937 en área y 0,991 en volumen).

**Fuera del alcance:** tendencias temporales de pérdida de hielo (el inventario es transversal), modelos predictivos, cruce con datos climáticos externos y relaciones entre área y volumen, porque una depende de la otra.

**Mapa conceptual:** [`docs/f1/mcdi500_s1_grupo3.pdf`](docs/f1/mcdi500_s1_grupo3.pdf) (versión 2, ajustada según la retroalimentación de la Formativa 1; editable en `docs/f1/mapa_conceptual_fase1.drawio`).

## Datos

| | |
|---|---|
| Fuente | Dirección General de Aguas (DGA), *Inventario Público de Glaciares de Chile 2022*. Descarga: https://dga.mop.gob.cl/inventario-publico-glaciares/ |
| Licencia | La página de descarga de la DGA no declara una licencia (revisada el 11-11-2026). Se usa como dato público con fines académicos, citando la fuente |
| Archivo original | `data/raw/Inventario_Publico_de_Glaciares_2022.csv` (26.180 filas × 45 columnas, 9,46 MB) |
| Huella SHA-256 | `5691de5d7d7ffe2c8586a7066e227ac5cc91fa1ec69f54096e937a054c283f1d` |
| Datos limpios (F2) | `data/processed/glaciares_limpio.csv` (26.180 × 48): variables en unidades físicas, banderas y derivadas. Entrada de F3 y F4; leerlo con `utl.cargar_limpio`, que restaura el orden de las ordinales y los códigos como texto |
| Matriz numérica (F2) | `data/processed/glaciares_modelo.csv` (26.180 × 47): ordinales, seno/coseno, one-hot, banderas y 4 continuas escaladas (sin `LOG_VOL` ni `ESP_MED`, redundantes con el área) |
| Perfil de calidad | [`docs/validacion_dataset.md`](docs/validacion_dataset.md) (original, generado con `python validar_dataset.py data/raw/Inventario_Publico_de_Glaciares_2022.csv --informe docs/validacion_dataset.md`) y `data/processed/perfil_glaciares_limpio.csv` (procesado) |
| Evaluación del dataset | [`docs/evaluacion_criterios_dataset.csv`](docs/evaluacion_criterios_dataset.csv): requisitos del curso; cumple los obligatorios con 2 avisos (variables sobre 60 % de faltantes y licencia no declarada) |
| Diccionario de variables | [`docs/diccionario_variables.csv`](docs/diccionario_variables.csv): 45 variables con su rol analítico |
| Bitácora y metadatos | [`docs/bitacora_f2.md`](docs/bitacora_f2.md) y [`docs/metadatos_proyecto.csv`](docs/metadatos_proyecto.csv), generados por F2 con las cifras de cada decisión |

El archivo de `data/raw/` **nunca se modifica**. F1 y F2 verifican su huella SHA-256 y se detienen si el archivo cambió.

## Estructura del repositorio

```text
proyecto-grupo3-mcdi500/
├── F1/
│   └── F1_Definicion.ipynb          # Problema, objetivos, entorno y reconocimiento del inventario
├── F2/
│   └── F2_Procesamiento.ipynb       # Obtención → exploración → limpieza → transformación → validación
├── data/
│   ├── raw/                         # CSV original de la DGA (inmutable)
│   └── processed/                   # Salidas de F2 (se regeneran al ejecutar el notebook)
├── src/
│   ├── utilidades.py                # Módulo compartido: rutas, huella, carga, entorno, Git, pruebas, Bitacora
│   ├── limpieza.py                  # F3: funciones de limpieza y codificación de F2 (programación estructurada)
│   ├── imputacion.py                # F3: estrategias de imputación intercambiables (patrón Strategy)
│   ├── transformadores.py           # F3: clase base Transformador y una clase hija por paso de F2
│   ├── pipeline.py                  # F3: Pipeline (composición) y observadores de la bitácora (patrón Observer)
│   ├── procesamiento.py             # F3: arma los pipelines de F2 y verifica las salidas byte a byte
│   └── pruebas_nucleo.py            # F3: 29 pruebas (casos normales, límite y excepciones)
├── docs/
│   ├── validacion_dataset.md        # Perfil de las 45 variables (validar_dataset.py)
│   ├── diccionario_variables.csv    # Generado por F1
│   ├── evaluacion_criterios_dataset.csv   # Generado por F1
│   ├── vinculacion_mapa_conceptual.csv    # Generado por F1
│   ├── metadatos_fase1.json         # Condiciones de ejecución de F1
│   ├── bitacora_f2.md               # Bitácora de decisiones exportada por F2
│   ├── metadatos_proyecto.csv       # Metadatos del pipeline aplanados por F2 (recursividad)
│   ├── f1/                          # Mapa conceptual de la Formativa 1 (.drawio y .pdf)
│   └── informe/                     # Informe técnico de la Sumativa 1 (.docx y .pdf)
├── validar_dataset.py               # Validador de dataset entregado por el curso
├── requirements.txt                 # Dependencias con versión exacta (pip freeze)
├── .mailmap                         # Unifica las identidades del historial (una por integrante)
├── .gitignore
└── README.md
```

Las funciones que usan varias fases viven en `src/utilidades.py`: F1 lo prueba con casos normales, límite y excepciones, y F2 lo importa, así que ninguna función está copiada entre notebooks. En la Fase 3, el pipeline de F2 se reorganiza en clases sin cambiar ningún resultado:

- Cada paso hereda de `Transformador`, que separa lo que el paso aprende (`ajustar`) de lo que aplica (`transformar`).
- `Pipeline` recorre los pasos sin preguntar su tipo y avisa a sus observadores, que generan la bitácora.
- La imputación recibe la estrategia como parámetro.

La verificación regenera los tres CSV de `data/processed/` y comprueba que son idénticos byte a byte a los de F2:

```bash
python src/pruebas_nucleo.py   # 29 pruebas: 11 normales, 5 límite y 13 excepciones
python src/procesamiento.py    # 15 pasos en 3 pipelines + comparación SHA-256 con F2
```

Las carpetas `F3/` y `F4/` se crearán al integrar los componentes de esas fases.

## Entorno y dependencias

- **Python:** 3.12 o superior. El proyecto se probó con Python 3.12.3 y 3.14.6.
- **Librerías principales:** pandas 3.1.1, NumPy 2.5.4, scikit-learn 1.9.1 (escaladores de F2), Matplotlib 3.11.2 (gráficos de control de F2), JupyterLab 4.6.6 e ipykernel 7.4.0. seaborn 0.13.2 queda instalada para F4.
- **Semilla:** `SEMILLA = 42`, declarada en `src/utilidades.py` y fijada en ambos notebooks. El pipeline actual es determinista, pero la semilla queda fijada para cualquier paso aleatorio de las fases siguientes.
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

Registrar el entorno como kernel de Jupyter (con el entorno activado). Se hace **una sola vez por equipo**; solo se repite si se vuelve a crear el `.venv` o se mueve la carpeta del proyecto:
```bash
python -m ipykernel install --user --name grupo3 --display-name "Python (.venv grupo3)"
```

## Ejecución de los notebooks

Ejecútalos **en orden** con el kernel del entorno virtual. Abre JupyterLab con el entorno activado, selecciona el kernel con *Kernel → Change Kernel → «Python (.venv grupo3)»* y usa *Kernel → Restart Kernel and Run All Cells*.

```bash
python -m jupyter lab
```

1. **`F1/F1_Definicion.ipynb`**
   - Presenta el problema, la pregunta, los objetivos, el alcance, las restricciones y los supuestos.
   - Importa y prueba `src/utilidades.py` y verifica la huella del dataset y las versiones del entorno.
   - Construye el diccionario de las 45 variables con su rol analítico y evalúa el dataset contra los criterios del curso.
   - Vincula el mapa conceptual con lo implementado y valida la fase.
   - **No modifica el inventario.** Solo genera artefactos documentales en `docs/`.
   - Resultado esperado: 13/13 pruebas del módulo OK, «Verificación F1 superada» y las seis comprobaciones `[OK]` de `validar_fase1`.
2. **`F2/F2_Procesamiento.ipynb`**
   - Sigue los pasos 6 a 11 del curso: exploración y medición → limpieza e imputación → transformación por tipo de variable → escalamiento → validación y pruebas → persistencia y bitácora.
   - Incluye gráficos de control (imputación, transformación y escalamiento) y una sección de recursividad.
   - Nunca modifica `original`: cada etapa produce su propio DataFrame. El CSV original se verifica con su huella SHA-256 al inicio y al final.
   - Exporta `glaciares_limpio.csv` y `glaciares_modelo.csv` a `data/processed/`, y la bitácora y los metadatos a `docs/`.
   - Resultado esperado: 17/17 validaciones OK, 23/23 pruebas OK, 8 pruebas de las funciones recursivas OK y «F2 finalizada».

También pueden ejecutarse sin abrir JupyterLab:

```bash
jupyter nbconvert --to notebook --execute --inplace F1/F1_Definicion.ipynb
jupyter nbconvert --to notebook --execute --inplace F2/F2_Procesamiento.ipynb
```

Los notebooks pueden ejecutarse desde su propia carpeta o desde la raíz del repositorio y no requieren internet. Cada etapa de F2 produce su propio DataFrame, así que re-ejecutar una celda suelta da el mismo resultado.

### Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError` (p. ej. `sklearn`) o «Faltan [...]: ejecutar pip install» | El kernel no es el del entorno virtual | En VS Code o JupyterLab, seleccionar el kernel de `.venv`; si persiste, `python -m pip install -r requirements.txt` con el entorno activado |
| JupyterLab no muestra el kernel del entorno virtual, o la sección 5 de F1 indica que el kernel no corre dentro de `.venv` | JupyterLab se abrió sin activar el entorno (p. ej., desde Anaconda o un acceso directo) | Activar el entorno, registrar el kernel con `python -m ipykernel install --user --name grupo3 --display-name "Python (.venv grupo3)"`, abrir con `python -m jupyter lab` y elegir *Kernel → Change Kernel → «Python (.venv grupo3)»* |
| `Activate.ps1 cannot be loaded… running scripts is disabled` (Windows) | PowerShell bloquea los scripts locales | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y volver a activar el entorno |
| La celda de entorno muestra `DIFIERE` o «← requirements.txt declara …» | Versiones distintas a las del proyecto | Es un aviso: los notebooks también corren con pandas 2.2, pero para reproducir exactamente usar el `.venv` del proyecto |
| `AssertionError: El CSV no coincide con la versión registrada` | `data/raw/` fue modificado o es otra versión. En Windows, un clon anterior a `.gitattributes` tiene el CSV con saltos de línea CRLF | Borrar el CSV y restaurarlo desde Git: `Remove-Item data\raw\*.csv` (Windows) o `rm data/raw/*.csv`, y luego `git checkout -- data/raw/` |
| `FileNotFoundError: No se encontró data/raw/...` o `src/utilidades.py` | El notebook se abrió fuera del repositorio clonado | Abrir el notebook desde la carpeta del repositorio |
| Los commits no aparecen asociados a tu perfil en GitHub | El email de Git no es el de la cuenta de GitHub (p. ej. `usuario@equipo.local`) | `git config user.email "email@de-la-cuenta"` antes de hacer commits |

## Decisiones principales de la Fase 2

| Hallazgo | Decisión |
|---|---|
| `CUBIERTO`, `OBSERVACIO` (100 % vacías); `Id`, `DATUM`, `HUSO`, `F_ESP_MED` (valor único); `WGI_1` (≡ `CLASIFICA`); `OBJECTID` (no único) | Se descartan. Los valores constantes quedan registrados en la bitácora |
| `CH_CASQ` 97,24 % faltante | Se descarta como categoría (> 60 %) y se conserva como bandera binaria `EN_CAMPO_HIELO` (723 glaciares) |
| Texto con codificación rota (`FOTOGRAMETR├ìA`), mayúsculas inconsistentes y espacios dobles | Se normaliza: 139 valores corregidos |
| `LATITUD`/`LONGITUD` como texto; `FUEN_FECHA` en 3 formatos; códigos leídos como enteros | Casting a `float`, a fecha más `FUEN_ANIO` (1955–2022) y a texto, respectivamente |
| 362 `VOL_km3 = 0` y 668 `EQ_AGUAKM3 = 0` (redondeo) | Se recalculan con la fórmula del propio inventario (factores distintos para glaciares rocosos); bandera de recálculo |
| 33 `HMIN = 0` en frentes de tierra o lago (faltante encubierto) | Se imputan con `HMEDIA − desnivel mediano por comuna`: es el único método sin violaciones físicas y con menor cambio de desviación (−0,003 %). Eliminar filas perdería 967,5 km² de hielo |
| 1 glaciar con `HMEDIA < HMIN` | Punto medio `(HMIN + HMAX) / 2`, con bandera |
| Área y volumen muy asimétricos (asimetría 43 y 54): el 1 % mayor reúne el 93,8 % del volumen | No se eliminan atípicos. Se aplica log10 (asimetría 0,6–0,7) y luego RobustScaler, elegido tras comparar los tres escaladores porque `RANGO_ALT` (4,05) y `HMEDIA` (1,45) conservan colas largas |
| `LOG_VOL` y `ESP_MED` son funciones del área (Spearman ≈ 1 con `LOG_AREA`) | Se excluyen de la matriz escalada; se conservan en `glaciares_limpio` |
| El CSV no conserva tipos: las ordinales se releen en orden alfabético y los códigos como enteros | `utl.cargar_limpio` restaura el orden declarado y los tipos; F2 lo comprueba al releer |
| Nominales, ordinal (`MZON_GLAC`) y cíclica (`ORIENTA`) | One-hot (32 columnas), orden geográfico declarado y seno/coseno |

Ningún glaciar se elimina: el resultado conserva las 26.180 filas. Las cifras y la justificación de cada decisión están en el notebook F2 y en [`docs/bitacora_f2.md`](docs/bitacora_f2.md).

## Control de versiones

- Cada integrante usa una sola identidad de Git, la de su cuenta de GitHub, y desarrolla su componente en una rama propia que se integra a `main` con un pull request revisado por otro integrante.
- Los commits usan prefijos por tipo de cambio: `feat:`, `fix:`, `test:`, `perf:`, `docs:`, `chore:`.
- En F1 y F2 el desarrollo quedó a cargo de Francisco Correa Soto, con autorización del docente. Desde la Fase 3, cada integrante desarrolla un componente técnico propio.
- El historial anterior tiene varias identidades por persona; `.mailmap` las unifica en `git log` y `git shortlog -sne`.
- Las tareas se desarrollan en ramas propias (`f1-ajustes`, `f2-pipeline`, …) y se integran a `main` mediante Pull Request (#1 a #6); las correcciones menores posteriores se hicieron directamente sobre `main`.
- No se versionan `.venv/`, las cachés de Python, `.env` ni la carpeta `material/` con el material de clase.
- Los notebooks se versionan **con sus salidas**, que sirven como evidencia de ejecución.

## Verificación en un segundo equipo

Antes de la entrega, el repositorio se clona desde GitHub en un equipo distinto del de desarrollo, se crea el `.venv` desde `requirements.txt` y se ejecutan F1 y F2 de principio a fin:

| Fecha | Integrante | Sistema operativo y Python | F1 | F2 | Observaciones |
|---|---|---|---|---|---|
| 11-11-2026| Gustavo Aloy Angella | Window 11 -Python 3.13.14  | OK (13/13) pruebas del módulo | OK (17/17) pruebas del módulo | Se detectaron y corrigieron dos problemas. Jupytelab no mostraba el kernel del .env y problemas con reconocer el cvs valido |

## Criterios de reproducibilidad

- No modificar los archivos de `data/raw/`.
- Usar rutas relativas y declarar las versiones de las dependencias.
- Ejecutar los notebooks de principio a fin con el kernel del entorno virtual antes de cada entrega.
- Antes de entregar, se clona el repositorio en un equipo distinto, se reconstruye el entorno y se ejecutan ambos notebooks.
