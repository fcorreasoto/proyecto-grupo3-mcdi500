# Changelog · Proyecto MCDI500 Grupo 3

Registro de cambios por fase, con el commit que los respalda y el motivo. Los hashes son los de `main`
(`git log --oneline`). Formato inspirado en *Keep a Changelog*.

## [F4] 2026-11-23 a 2026-11-24 · Visualización y comunicación

### Agregado
- `src/comunicacion.py` y `src/pruebas_comunicacion.py` (`431ac94`, PR #14, Francisco Correa Soto).
  Carga de artefactos, contrato con F3 recalculado con `concentracion.py`, copia interpretable desde
  `glaciares_modelo` y tablas para graficar. 23 pruebas. Responde al criterio de preprocesamiento para
  visualización: se demuestra que la matriz de modelo y la copia interpretable son el mismo dato.
- `src/figuras.py`: clase base `FiguraHallazgo` y figuras principales 1–3, con sus pruebas (`0746a7f`, PR #15,
  Gustavo Aloy Angella). El título-hallazgo se arma con las cifras de la propia tabla de la figura.
- `src/figuras.py`: figuras complementarias 4–6 y sus pruebas (`c5d9daa`, PR #16, Roberto Gaubert Urbina).
  La figura 6 controla por macrozona la asociación entre tipo de glaciar y concentración.
- `F4/F4_Comunicacion.ipynb`, `F4/README.md`, seis figuras y tres anexos, `docs/hallazgos_f4.csv` y
  `docs/metadatos_f4.json` (`463312b`, PR #17, Roberto Gaubert Urbina). Ejecutado de principio a fin:
  contrato 8/8 y 65/65 pruebas.
- `docs/changelog.md` (este archivo, PR #18).

### Agregado tras la retroalimentación de la Fase 4 (rama `f4-theil`)
- `IndiceTheil` y `descomponer_theil` en `src/concentracion.py`, con 8 pruebas (commit `XXXXXXX`, PR #XX).
  Convierten en una cifra la inferencia de F3: la clasificación da cuenta del 77,6 % de la desigualdad
  de la superficie y la región del 5,7 %. El Gini no se descompone de forma exacta; Theil sí.
- Figura 3 de la descomposición de Theil, como figura principal de resolución (commit `XXXXXXX`).

### Cambiado tras la retroalimentación de la Fase 4
- Figura 2: barras pareadas (% de glaciares y % de superficie por clasificación) en vez de barras
  apiladas, con el título «El 0,8 % de los glaciares, los efluentes, reúne el 65,4 % de la superficie».
- Volumen como magnitud secundaria (figura 7): el título explica por qué su concentración es mayor
  (exponente 1,357).
- Redacción: «se concentra» y «se asocia»; el inventario como fotografía de 2022 con imágenes de
  distintos años. Figuras renumeradas (fig1–fig7) y 76 pruebas en el notebook F4.

### Cambiado
- `README.md`: F4 implementada, estructura, ejecución, pruebas y resultados de la fase (PR #18).
- F1 reejecutado y sus metadatos actualizados antes de abrir las ramas de F4 (`c78b65c`).

## [F3] 2026-11-16 a 2026-11-18 · Núcleo algorítmico

### Agregado
- Funciones de limpieza y estrategias de imputación con patrón Strategy (`bc3c1da`).
- Transformadores, pipeline con patrón Observer y verificación byte a byte con F2 (`37f2d13`, PR #8).
- Concentración de la superficie y del volumen derivado del área (`a1d8d95`, PR #9).
- Medición reproducible con `timeit`/`tracemalloc`, comparación de implementaciones y recursividad (`48763fc`).
- Notebook F3 (`e68081e`, Gustavo Aloy Angella, PR #10; `b2c136c` y `3e1e878`, Roberto Gaubert Urbina, PR #11 y #12).
- README de la carpeta F3 (`6bc9ed0`, Roberto Gaubert Urbina) y referencias bibliográficas (`71ef541`, Gustavo Aloy Angella).

### Cambiado
- Normalización del texto por valores únicos en vez de fila a fila (`f1ead4d`). La medición de la
  sección 7.4 de F3 mostró menos llamadas y menos memoria con el mismo resultado.
- Identidades de Git unificadas con `.mailmap` (`0334b4e`, `e558c93`): una identidad por integrante.

### Corregido
- `procesamiento.py` escribía los CSV con `\r\n` en Windows y la verificación byte a byte fallaba (`e68081e`).
- `metadatos_f3` registraba `HEAD` y cambiaba en cada ejecución; ahora registra el último commit de
  `src/` y `data/raw` (`7098b65`).

## [F1–F2] 2026-11-11 · Definición y procesamiento

### Cambiado
- Informe alineado con el mapa conceptual v2, ajustado según la retroalimentación de la Formativa 1 (`fcc0311`, `06a731e`).
- Integrantes actualizados según el acta en README, notebooks y mapa conceptual (`4efce1e`).

### Corregido
- Tipos al releer `glaciares_limpio`, variables redundantes y trazabilidad de F2 (`a22cd90`).
- F1 y F2 ejecutados completos con sus salidas (`7c65f7b`); `pandas` faltaba en la celda de importaciones de F1 (`16f7562`).
- Git convertía los saltos de línea de los CSV en Windows y la huella SHA-256 no coincidía (`1ef407b`).
- Verificación de F1 y F2 en un segundo equipo con Windows (`a03f745`, Gustavo Aloy Angella, PR #7).
