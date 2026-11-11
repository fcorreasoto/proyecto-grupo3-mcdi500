# Bitácora de decisiones · F2

| # | Etapa | Decisión | Evidencia |
|---|---|---|---|
| 1 | obtención | Se carga el CSV oficial desde data/raw sin modificarlo | 26,180 filas × 45 columnas; SHA-256 5691de5d7d7f… = referencia |
| 2 | exploración | Id no aporta información (valor único) | 0.0 % faltante; 1 valor(es) único(s); valor = 0 |
| 3 | exploración | DATUM no aporta información (valor único) | 0.0 % faltante; 1 valor(es) único(s); valor = WGS 84 |
| 4 | exploración | HUSO no aporta información (valor único) | 0.0 % faltante; 1 valor(es) único(s); valor = 19 SUR |
| 5 | exploración | CH_CASQ no aporta información (faltantes > 60%) | 97.24 % faltante; 6 valor(es) único(s) |
| 6 | exploración | CUBIERTO no aporta información (faltantes > 60%) | 100.0 % faltante; 0 valor(es) único(s) |
| 7 | exploración | F_ESP_MED no aporta información (valor único) | 0.0 % faltante; 1 valor(es) único(s); valor = CHEN & OHMURA 1990 |
| 8 | exploración | OBSERVACIO no aporta información (faltantes > 60%) | 100.0 % faltante; 0 valor(es) único(s) |
| 9 | exploración | COD_GLA es el identificador; OBJECTID no identifica filas | COD_GLA único en 26,180 filas; OBJECTID repetido en 102 filas; 0 filas duplicadas |
| 10 | exploración | Área y volumen son muy asimétricos, con atípicos legítimos | AREA_KM2: asimetría 43.1, media 0.803 vs. mediana 0.036 km², 14.37 % fuera del IQR; VOL_km3: asimetría 54.0 |
| 11 | exploración | VOL_km3 = 0 es redondeo, no ausencia de hielo | 362 glaciaretes de área ≤ 0,002 km²; la fórmula reproduce el volumen (razón mediana 0.9999; rocosos 0.6 = 60 % de hielo) |
| 12 | exploración | EQ_AGUAKM3 es una proporción fija de VOL_km3 según el tipo | EQ/VOL mediana 0.85 (850 kg/m³) y 0.917 en rocosos; 668 ceros por redondeo |
| 13 | exploración | HMIN = 0 con frente en tierra o lago es un faltante encubierto | 69 glaciares con HMIN = 0: 36 en fiordo (plausible) y 33 en tierra/lago (implausible) |
| 14 | exploración | Un glaciar viola HMIN ≤ HMEDIA ≤ HMAX | CL108116007@ (ÑUBLE): HMEDIA 2,228 m < HMIN 2,849 m |
| 15 | exploración | WGI_1 duplica la información de CLASIFICA | correspondencia uno a uno entre las 5 clases y los códigos WGI_1: True |
| 16 | exploración | Revisión de categorías: codificación, mayúsculas, espacios y variantes | NOMBRE: 'VOLCAN PLANCHON  PETEROA' (espacios irregulares); FUENTE_DIG: 'LiDAR ANDINA' (mayúsculas inconsistentes); FUENTE_DIG: 'FOTOGRAMETR├ìA' (codificación de caracteres); NOM_CUEN: 'COSTERAS ENTRE LAG.  BLANCA(INC), SENO OTWAY, CANAL JERONIMO Y MAGALLANES' (espacios irregulares) |
| 17 | exploración | FUEN_FECHA mezcla formatos; LATITUD/LONGITUD son texto con coma decimal | DD/MM/AAAA: 26,167, AAAA: 12, MM/DD/AAAA: 1; ejemplo LATITUD '-18,1744803305003' |
| 18 | limpieza | Se descartan 9 columnas: Id, DATUM, HUSO, CUBIERTO, F_ESP_MED, OBSERVACIO, WGI_1, OBJECTID, CH_CASQ | 100 % vacías (CUBIERTO, OBSERVACIO), valor único (Id, DATUM = WGS 84, HUSO = 19 SUR, F_ESP_MED = CHEN & OHMURA 1990), redundante (WGI_1 ≡ CLASIFICA), sin unicidad (OBJECTID), CH_CASQ > 60 % faltante (45 → 36 columnas originales) |
| 19 | limpieza | CH_CASQ se convierte en la bandera binaria EN_CAMPO_HIELO | el faltante significa 'no pertenece'; 723 glaciares pertenecen a un campo de hielo o casquete |
| 20 | limpieza | Se normaliza el texto (codificación, mayúsculas y espacios) | 139 valores corregidos (NOMBRE: 5, FUENTE_DIG: 6, NOM_CUEN: 128): 'FOTOGRAMETR├ìA' → 'FOTOGRAMETRÍA', 'LiDAR ANDINA' → 'LIDAR ANDINA' y espacios dobles en nombres |
| 21 | limpieza | Casting: LATITUD/LONGITUD a float, FUEN_FECHA a fecha + FUEN_ANIO, códigos a texto | 26,180 coordenadas convertidas sin pérdida; 26,168 fechas completas y 26,180 años (1955–2022); 8 columnas de código a texto |
| 22 | limpieza | Se recalculan los ceros de VOL_km3 y EQ_AGUAKM3 con la fórmula del inventario | 362 volúmenes y 668 equivalentes; volumen total +0.001333 km³ (despreciable); banderas VOL/EQ_RECALCULADO |
| 23 | imputación | HMIN = 0 en tierra/lago se marca como faltante e imputa con 'HMEDIA − desnivel mediano por comuna' | 33 valores (0.13 %); cambio de desv. estándar -0.0029 %; violaciones de HMIN ≤ HMEDIA: media global 33, mediana global 31, mediana por comuna 14, HMEDIA − desnivel mediano por comuna 0; eliminar filas perdería 967.5 km² de hielo |
| 24 | imputación | HMEDIA incoherente se reemplaza por (HMIN + HMAX) / 2 | 1 glaciar; la mediana global (1,525 m) violaría HMIN ≤ HMEDIA; el punto medio da 2,893 m |
| 25 | transformación | Se derivan RANGO_ALT, LOG_AREA, LOG_VOL, CLASE_TAMANO, FRENTE_AGUA y FUENTE_GRUPO | log10 reduce la asimetría del área de 43.1 a 0.61 y del volumen de 54.0 a 0.69; cortes de tamaño [0.01, 0.1, 1, 10] km² |
| 26 | transformación | MZON_GLAC y CLASE_TAMANO se codifican como ordinales con orden declarado | orden geográfico NORTE → AUSTRAL; el alfabético pondría AUSTRAL < CENTRO < NORTE < SUR |
| 27 | transformación | ORIENTA se codifica con seno y coseno | variable circular (N = 0°, NW = 315° son vecinas); 3 laderas PLANO → (0, 0) |
| 28 | transformación | One-hot para CLASIFICA, FRENTE_TER, REGION y FUENTE_GRUPO | nominales sin orden; 32 columnas binarias; FUENTE_DIG: 19 → 8 categorías (< 1 % → OTRAS) |
| 29 | escalamiento | Se usa RobustScaler (mediana 0, RIC 1) sobre 6 variables continuas | LOG_AREA, LOG_VOL, HMEDIA, RANGO_ALT, PENDIENTE, ESP_MED; coherente con la imputación por mediana y con los atípicos legítimos; sobre el área sin log, MinMax deja el 99.0 % de los datos en el 1 % inferior del rango |
| 30 | validación | Se ejecutan 17 validaciones del dataset resultante | 17/17 OK: filas, clave, nulos, tipos, one-hot, ordinales, RobustScaler, reglas físicas, banderas y huella de data/raw |
| 31 | validación | Se ejecutan 21 pruebas de las funciones | 21/21 OK: 7 casos normales, 5 casos límite y 9 excepciones |
| 32 | documentación | Los metadatos del pipeline se aplanan con una función recursiva | 4 niveles de anidamiento → 31 pares clave-valor en docs/metadatos_proyecto.csv; 8 pruebas OK (normales, límite y excepción) |
| 33 | persistencia | Se guardan y releen glaciares_limpio.csv y glaciares_modelo.csv en data/processed | limpio 26180×48 y modelo 26180×49; forma, columnas y tipos comprobados tras releer; data/raw intacto |
