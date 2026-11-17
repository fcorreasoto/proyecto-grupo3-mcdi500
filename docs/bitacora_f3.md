# Bitácora de decisiones · F3

| # | Etapa | Decisión | Evidencia |
|---|---|---|---|
| 1 | limpieza | Se descartan columnas sin información y redundantes; CH_CASQ pasa a EN_CAMPO_HIELO | descartadas = 9; EN_CAMPO_HIELO = 723 |
| 2 | limpieza | Se normaliza el texto (codificación, mayúsculas y espacios) | valores_corregidos = 139; por_columna = {'NOMBRE': 5, 'FUENTE_DIG': 6, 'NOM_CUEN': 128} |
| 3 | limpieza | Casting: coordenadas a float, FUEN_FECHA a fecha + FUEN_ANIO, códigos a texto | coordenadas_nulas = 0; fechas_completas = 26168; anios = 26180 |
| 4 | limpieza | Se recalculan los ceros de VOL_km3 y EQ_AGUAKM3 con la fórmula del inventario | volumenes = 362; equivalentes = 668 |
| 5 | limpieza | Los faltantes encubiertos de HMIN y HMEDIA se marcan como NaN | HMIN = 33; HMEDIA = 1 |
| 6 | limpieza | HMIN se imputa con la estrategia elegida por la regla declarada | metodo = HMEDIA − desnivel mediano por comuna; imputados = 33 |
| 7 | limpieza | HMEDIA incoherente se reemplaza por (HMIN + HMAX) / 2 | imputados = 1 |
| 8 | limpieza | Se derivan RANGO_ALT, LOG_AREA, LOG_VOL, CLASE_TAMANO, FRENTE_AGUA y FUENTE_GRUPO | asimetria_log_area = 0.61; asimetria_log_vol = 0.69 |
| 9 | modelo | One-hot para CLASIFICA, FRENTE_TER, REGION y FUENTE_GRUPO | columnas_binarias = 32 |
