F4 · Visualización y comunicación de resultados
================================================

Notebook: F4_Comunicacion.ipynb

Propósito
---------
Cierra el proyecto. No vuelve a limpiar ni a transformar: recibe lo que dejaron
F2 y F3 en data/processed/, verifica que cumple lo prometido y responde con
figuras la pregunta de investigación. Cada figura responde un objetivo y su
título dice el hallazgo, con la cifra que lo respalda.

Contenido
---------
 0–1  Entorno, trazabilidad, huella de data/raw y objetivo de la fase.
 2    Artefactos de F2 y F3: contrato (recálculo con concentracion.py) y
      verificación independiente contra data/raw (Gini por otra fórmula).
 3    Dos versiones del dato: la matriz de modelo (escalada, one-hot) se
      revierte y se compara con la copia interpretable (glaciares_limpio).
 4    Vinculación objetivo → figura.
 5    Figuras principales en tres actos: curva de Lorenz (contexto), barras
      pareadas por clasificación (contraste) y descomposición de Theil
      (resolución: cuánto de la desigualdad se asocia a cada agrupación).
 6    Figuras complementarias: tamaño por tipo, regiones, control por
      macrozona (¿la concentración persiste sin los efluentes?) y el volumen
      como magnitud secundaria (por qué está más concentrado).
 7    Decisiones de escala: lineal frente a logarítmica.
 8    Eficiencia: tres implementaciones de la participación por grupo,
      con timeit y tracemalloc sobre tamaños crecientes.
 9    Validación: pruebas de F4 (comunicación y figuras) y de F3 (concentración).
 10   Persistencia de figuras, hallazgos y metadatos.
 11   Relato en tres actos, discusión, limitaciones, comparación con fases
      previas y conclusiones.

Entradas (no se modifican)
--------------------------
- data/processed/glaciares_limpio.csv            (F2, copia interpretable)
- data/processed/glaciares_modelo.csv            (F2, matriz escalada y one-hot)
- data/processed/concentracion_magnitudes_f3.csv (F3)
- data/processed/concentracion_region_f3.csv     (F3)
- data/processed/concentracion_clasificacion_f3.csv (F3)
- data/processed/concentracion_macrozona_f3.csv  (F3)
- data/processed/lorenz_f3.csv                   (F3)
- data/raw/Inventario_Publico_de_Glaciares_2022.csv (solo para verificar)

Módulos
-------
- src/comunicacion.py   carga y contrato con F3, copia interpretable, tablas
                        para graficar (composición, participación cruzada,
                        Gini por grupo) y formato castellano de las cifras.
- src/figuras.py        clase base FiguraHallazgo (método plantilla
                        construir) y una clase hija por figura.
- src/concentracion.py  (F3, ampliado en F4) IndiceTheil y descomponer_theil:
                        desigualdad entre y dentro de los grupos.
- src/pruebas_comunicacion.py   24 pruebas (normales, límite, excepciones y control).
- src/pruebas_figuras.py        20 pruebas, incluidas las cifras de cada título.
- src/pruebas_concentracion.py  32 pruebas, 8 de ellas de Theil (agregadas en F4).

Salidas (se regeneran al ejecutar el notebook)
----------------------------------------------
- F4/figuras/fig1_lorenz_superficie.png          principal · contexto
- F4/figuras/fig2_composicion_clasificacion.png  principal · contraste
- F4/figuras/fig3_descomposicion_theil.png       principal · resolución
- F4/figuras/fig4_tamano_por_clasificacion.png   complementaria
- F4/figuras/fig5_superficie_por_region.png      complementaria
- F4/figuras/fig6_tipo_por_macrozona.png         complementaria
- F4/figuras/fig7_volumen_derivado.png           complementaria · magnitud secundaria
- F4/figuras/anexo1..3_*.png                     anexos (secciones 3, 7 y 8)
- docs/hallazgos_f4.csv     una fila por figura: objetivo, hallazgo y evidencia.
- docs/metadatos_f4.json    versiones, semilla, huella de data/raw, commit,
                            entradas, figuras y número de pruebas.

Ejecución
---------
Después de F1, F2 y F3, con el entorno virtual activado (ver README.md raíz):

    jupyter nbconvert --to notebook --execute --inplace F4/F4_Comunicacion.ipynb

o en JupyterLab: Kernel → Restart Kernel and Run All Cells.

Las pruebas también se ejecutan desde la raíz:

    python src/pruebas_comunicacion.py
    python src/pruebas_figuras.py

Resultado esperado
------------------
- Contrato con F3: 8/8 controles cumplidos; las cifras se reproducen desde data/raw.
- Copia reconstruida desde glaciares_modelo = glaciares_limpio = data/raw.
- 76/76 pruebas (24 de comunicación, 20 de figuras y 32 de concentración, con Theil).
- Siete figuras y tres anexos en F4/figuras/, a 200 ppp.
- «data/raw intacto (SHA-256 igual al inicial).»

Las mediciones de tiempo de la sección 8 varían entre equipos. Las cifras de
las figuras y las pruebas no cambian.

Hallazgos
---------
- El 1 % de los glaciares (261) reúne el 71,5 % de la superficie; Gini 0,937.
- El 0,8 % de los glaciares, los efluentes (217), reúne el 65,4 % de la
  superficie; 18.211 glaciaretes (69,6 %) aportan el 3,8 %.
- Descomposición de Theil (3,793): la diferencia entre clasificaciones da
  cuenta del 77,6 % de la desigualdad; entre macrozonas, del 6,5 %, y entre
  regiones, solo del 5,7 %.
- Dentro de cada tipo el Gini baja a 0,50–0,71: cada tipo ocupa su propio
  rango de tamaño.
- Los efluentes solo existen en la macrozona austral (73,5 % de su superficie);
  sin ellos el Gini baja a 0,837, pero la concentración persiste.
- El volumen es una magnitud secundaria: se calculó desde el área con
  exponente 1,357 (10 veces más área → 23 veces más volumen), por eso su Gini
  sube de 0,937 a 0,991. No es un hallazgo independiente.

Fase anterior: F3/F3_NucleoAlgoritmico.ipynb
