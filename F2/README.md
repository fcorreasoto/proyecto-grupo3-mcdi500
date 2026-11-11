F2 · Obtención, exploración, limpieza, transformación y validación
==================================================================

Notebook: F2_Procesamiento.ipynb

Propósito
---------
Convierte el inventario original de la DGA en un conjunto limpio, transformado y
validado para la Fase 3, siguiendo los pasos 6 a 11 del pipeline del curso:

    Obtener → Explorar → Limpiar → Transformar → Escalar → Validar → Persistir

Regla de trabajo: medir primero, decidir después y justificar con la medición.
El archivo de data/raw/ nunca se modifica y ningún glaciar se elimina: la salida
conserva las 26.180 filas.

Contenido
---------
 0–1  Entorno, módulo compartido (src/utilidades.py), bitácora y obtención de la
      fuente verificada con su huella SHA-256.
 2    Exploración y medición: tipos y faltantes, rangos y asimetría, concentración
      (el 1 % de los glaciares reúne el 93,8 % del volumen), faltantes encubiertos,
      coherencia física, redundancias y fechas. Incluye la verificación de que el
      espesor y el volumen se estimaron desde el área (Chen y Ohmura, 1990).
 3    Limpieza e imputación: columnas sin información, normalización del texto,
      casting de tipos, reconstrucción del volumen y comparación de métodos de
      imputación de altitudes.
 4    Transformación por tipo de variable: derivadas, ordinal, cíclica (seno/coseno)
      y one-hot.
 5    Escalamiento: comparación de tres escaladores y elección de RobustScaler.
 6    Validación técnica y pruebas: ensamblaje de las salidas, asserts del dataset y
      pruebas de casos normales, límite y excepciones.
 7    Recursividad: aplanado de los metadatos del pipeline.
 8    Persistencia, relectura verificada y bitácora completa.
 9–10 Trazabilidad (rama y commit), entrega a F3 y reflexión técnica.

Entradas
--------
- data/raw/Inventario_Publico_de_Glaciares_2022.csv   (26.180 × 45, solo lectura)
- src/utilidades.py

Salidas (se regeneran al ejecutar el notebook)
----------------------------------------------
- data/processed/glaciares_limpio.csv          26.180 × 48 · variables en unidades
                                               físicas, banderas y derivadas. Entrada
                                               de F3 y F4; leer con utl.cargar_limpio.
- data/processed/glaciares_modelo.csv          26.180 × 47 · matriz 100 % numérica.
- data/processed/perfil_glaciares_limpio.csv   Perfil de calidad del conjunto limpio.
- docs/bitacora_f2.md                          Bitácora de decisiones con sus cifras.
- docs/metadatos_proyecto.csv                  Metadatos del pipeline aplanados.

Ejecución
---------
Ejecutar después de F1, con el entorno virtual del proyecto activado (ver README.md
en la raíz):

    jupyter nbconvert --to notebook --execute --inplace F2/F2_Procesamiento.ipynb

o en JupyterLab: Kernel → Restart Kernel and Run All Cells. Puede ejecutarse desde
esta carpeta o desde la raíz del repositorio y no requiere internet. Cada etapa
produce su propio DataFrame, por lo que re-ejecutar una celda suelta da el mismo
resultado.

Resultado esperado
------------------
- 17/17 validaciones OK.
- 23/23 pruebas OK.
- 8 pruebas de las funciones recursivas OK.
- «F2 finalizada».

Decisiones principales
----------------------
- Se descartan columnas vacías, de valor único o redundantes; CH_CASQ (97,24 %
  faltante) se conserva como bandera EN_CAMPO_HIELO.
- Se normaliza el texto (139 valores corregidos) y se corrigen los tipos de
  coordenadas, fechas y códigos.
- VOL_km3 y EQ_AGUAKM3 iguales a 0 se recalculan con la fórmula del inventario
  (factores distintos para glaciares rocosos), con bandera.
- 33 HMIN = 0 en frentes de tierra o lago se imputan con HMEDIA menos el desnivel
  mediano por comuna, con bandera.
- No se eliminan atípicos: área y volumen se transforman con log10 y se escalan con
  RobustScaler. LOG_VOL y ESP_MED se excluyen de la matriz por depender del área.

El detalle y la justificación de cada decisión están en el notebook y en
docs/bitacora_f2.md.

Decisiones abiertas para F3
---------------------------
- El one-hot conserva todas las categorías; con modelos lineales habrá que eliminar
  una por grupo.
- 12 fechas solo traen el año: sirven para FUEN_ANIO, no para antigüedades en meses.
- Qué funciones de imputación, codificación y escalamiento se trasladarán a src/.

Fase anterior: F1/F1_Definicion.ipynb
