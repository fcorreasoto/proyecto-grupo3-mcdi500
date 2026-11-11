# MCDI500 · Grupo 3 — Análisis reproducible del Inventario Público de Glaciares de Chile 2022

Proyecto académico del curso **Programación para la Ciencia de Datos**, Magíster en Ciencia de Datos e Inteligencia Artificial.

## Integrantes
- Aníbal Reyes
- Francisco Correa
- Gustavo Aloy
- Roberto Gaubert

## Problemática
Los glaciares constituyen reservas de agua relevantes para Chile. Se requiere caracterizar su distribución territorial y las diferencias de superficie y volumen estimado utilizando un inventario oficial, con un procedimiento transparente y reproducible.

## Pregunta de investigación
¿Cómo se distribuyen los glaciares registrados en el Inventario Público de Glaciares 2022 según región, clasificación, superficie y volumen estimado?

## Objetivo general
Caracterizar la distribución territorial y las propiedades físicas de los glaciares registrados en el inventario mediante un flujo de análisis reproducible en Python.

## Objetivos específicos
1. Verificar la estructura, calidad y tipos de variables del inventario.
2. Documentar y ejecutar un procedimiento de limpieza y transformación sin alterar el archivo original.
3. Resumir número de glaciares, superficie y volumen estimado por región y clasificación.
4. Generar tablas y visualizaciones documentadas que puedan reproducirse desde el repositorio.

## Datos
- **Fuente:** Inventario Público de Glaciares de Chile 2022. Registrar organismo editor, enlace oficial, fecha de descarga y licencia tras su verificación.
- **Archivo utilizado:** `Inventario Publico de Glaciares 2022.dbf.csv`.
- **Dimensiones:** 26.180 registros y 45 columnas.
- **Validación:** el script oficial `validar_dataset.py` devuelve **CUMPLE**, con un aviso sobre columnas con más del 60% de valores faltantes.
- **Limitación:** un inventario transversal no permite estimar por sí solo tendencias temporales de pérdida de hielo.

## Estructura prevista
```text
MCDI500-grupo3/
├── data/
│   ├── raw/                 # Datos originales sin modificar
│   └── processed/           # Datos transformados
├── notebooks/
│   ├── 01_fase1_entorno.ipynb
│   └── 02_fase2_pipeline.ipynb
├── src/                     # Funciones reutilizables
├── docs/
│   ├── validacion_dataset.md
│   ├── diccionario_variables.md
│   └── decisiones_metodologicas.md
├── results/                  # Tablas y figuras
├── validar_dataset.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Instalación
Clonar el repositorio:
```bash
git clone https://github.com/fcorreasoto/MCDI500-grupo3.git
cd MCDI500-grupo3
```
Crear y activar un entorno virtual:

**Linux/macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Instalar las dependencias una vez que se haya generado `requirements.txt`:
```bash
pyton -m pip install --upgrade pip #update pip
python -m pip install -r requirements.txt
```


## Criterios de reproducibilidad
- No modificar los archivos de `data/raw/`.
- Documentar las transformaciones, los tipos de datos y los criterios para manejar faltantes.
- Usar rutas relativas y declarar las versiones de dependencias.
- Ejecutar los notebooks de principio a fin con el kernel del entorno virtual.
- No versionar `.venv/`, cachés ni archivos temporales.
- Registrar cambios mediante commits descriptivos de cada integrante.
