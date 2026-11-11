F1 · Definición del proyecto y entorno reproducible
====================================================

Notebook: F1_Definicion.ipynb

Propósito
---------
Presenta la problemática, la pregunta, los objetivos, el alcance, las restricciones
y los supuestos del proyecto; comprueba el entorno de ejecución y hace un
reconocimiento descriptivo del Inventario Público de Glaciares de Chile 2022 (DGA).

F1 no modifica el inventario: no elimina registros, no imputa valores ni transforma
variables. Esas decisiones se toman y se justifican en F2.

Contenido
---------
 1–3  Configuración documental, problemática, pregunta, objetivos, alcance,
      restricciones y supuestos.
 4    Organización del repositorio, módulo compartido (src/utilidades.py) y
      verificación de la huella SHA-256 del CSV original.
      4.1 Pruebas del módulo: casos normales, límite y excepciones.
 5    Verificación del entorno (versión de Python y librerías frente a requirements.txt).
 6    Reconocimiento inicial del inventario: roles analíticos previstos y hallazgos
      preliminares.
 7    Diccionario de las 45 variables, señales de calidad y evaluación del dataset
      contra los criterios del curso.
 8    Correspondencia con las fases F1–F4 y con el mapa conceptual.
 9    Persistencia de los artefactos, validación de la fase y trazabilidad con Git.
 10   Reflexión técnica, referencias y cierre de fase.

Entradas
--------
- data/raw/Inventario_Publico_de_Glaciares_2022.csv   (26.180 × 45, solo lectura)
- src/utilidades.py
- requirements.txt
- docs/f1/mapa_conceptual_fase1.drawio

Salidas (se regeneran al ejecutar el notebook)
----------------------------------------------
- docs/diccionario_variables.csv          45 variables con tipo, rol analítico y calidad.
- docs/evaluacion_criterios_dataset.csv   Requisitos del curso: cumple los obligatorios
                                          con 2 avisos (variables sobre 60 % de faltantes
                                          y licencia no declarada).
- docs/vinculacion_mapa_conceptual.csv    Elementos del mapa conceptual con su estado
                                          y evidencia.
- docs/metadatos_fase1.json               Condiciones de ejecución (Python, librerías,
                                          huella, commit).

Ejecución
---------
Con el entorno virtual del proyecto activado (ver README.md en la raíz):

    jupyter nbconvert --to notebook --execute --inplace F1/F1_Definicion.ipynb

o en JupyterLab: Kernel → Restart Kernel and Run All Cells. Puede ejecutarse desde
esta carpeta o desde la raíz del repositorio y no requiere internet.

Resultado esperado
------------------
- 13/13 pruebas del módulo OK.
- «Verificación F1 superada».
- Las seis comprobaciones [OK] de validar_fase1.

Hallazgos que pasan a F2
------------------------
- Columnas vacías o de valor único, y tres variables con más de 60 % de faltantes.
- Códigos leídos como enteros (COD_CUEN, CUT_COM) y coordenadas leídas como texto
  (LATITUD, LONGITUD).
- Faltantes encubiertos: 69 HMIN = 0, 362 VOL_km3 = 0 y 668 EQ_AGUAKM3 = 0 en
  columnas que el perfil reporta con 0 % de nulos.

Siguiente fase: F2/F2_Procesamiento.ipynb
