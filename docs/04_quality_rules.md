# Reglas, umbrales y política GX

Los sufijos por atributo identifican instancias distintas de una regla. El mapeo exacto se guarda en `*_suite.json` y `*_policy.json`: cada Expectation lleva `meta.rule_id`, severidad y requisitos. Toda regla crítica exige 100% de cumplimiento. Los nulos se verifican explícitamente porque una comprobación de rango por sí sola puede omitirlos.

| ID | Capa / atributo | Dimensión y regla | Métrica / umbral | Severidad | GX / justificación |
|---|---|---|---|---|---|
| *-COUNT | Todas / filas | Completitud: lote no vacío | filas >=1 | Critical | ExpectTableRowCountToBeBetween; evita éxito sin datos |
| S01 | Raw Spotify / columnas | Validez del contrato | Todas las columnas analíticas presentes | Critical | ExpectTableColumnsToMatchSet; AR1–3 |
| S02-* | Raw Spotify / ID y medidas | Completitud | nulos=0 | Critical | ExpectColumnValuesToNotBeNull; ID y métricas indispensables |
| S03 | Raw Spotify / popularity | Validez | 0 <= valor <=100 | Critical | ExpectColumnValuesToBeBetween; dominio de puntuación, no umbral ajustado a la muestra |
| S04-* | Raw Spotify / energy,danceability | Validez | 0 <= valor <=1 | Critical | ExpectColumnValuesToBeBetween; atributos normalizados |
| S05-* | Raw Spotify / artists,track_name | Completitud | nulos=0 | Warning | ExpectColumnValuesToNotBeNull; ausencias se aíslan sin invalidar todo el catálogo |
| S06 | Raw Spotify / track_id | Unicidad | duplicados=0 | Warning | ExpectColumnValuesToBeUnique; se espera incumplimiento por grano género-canción; transformación controla la multiplicidad |
| G01 | Raw Grammy / columnas | Validez del contrato | Columnas requeridas presentes | Critical | ExpectTableColumnsToMatchSet |
| G02 | Raw Grammy / source_row_id | Unicidad | duplicados=0 | Critical | ExpectColumnValuesToBeUnique; identidad de registro |
| G03-* | Raw Grammy / ID,año,categoría | Completitud | nulos=0 | Critical | ExpectColumnValuesToNotBeNull |
| G04 | Raw Grammy / year | Validez | 100% cuatro dígitos | Critical | ExpectColumnValuesToMatchRegex; conversión explícita segura |
| G05 | Raw Grammy / category | Completitud | blancos=0 | Critical | ExpectColumnValuesToNotMatchRegex; dimensión requerida |
| G06 | Raw Grammy / artist | Completitud | blancos=0 | Warning | ExpectColumnValuesToNotMatchRegex; perfilado detecta vacíos, estado missing_key |
| G07 | Raw Grammy / winner | Adecuación semántica | >=2 valores distintos | Warning | ExpectColumnUniqueValueCountToBeBetween; monitor de campo constante, no prueba de exactitud factual |
| P01 | Preparada / esquema | Validez | Columnas requeridas presentes | Critical | ExpectTableColumnsToMatchSet |
| P02 | Preparada / ID | Unicidad | duplicados=0 | Critical | ExpectColumnValuesToBeUnique; prohíbe fan-out |
| P03-* | Preparada / campos obligatorios | Completitud | nulos=0 | Critical | ExpectColumnValuesToNotBeNull |
| P04 | Preparada / match_status | Validez | dominio de 5 estados | Critical | ExpectColumnValuesToBeInSet |
| P05,P06-* | Preparada / métricas | Validez | popularidad [0,100], audio [0,1] | Critical | ExpectColumnValuesToBeBetween |
| P07-match_integrity | Preparada / columnas derivadas de control | Consistencia | 100% coherencia entre estado, candidatos, elegibilidad, clave y métricas | Critical | ExpectColumnValuesToBeInSet(True); evita métricas sin vínculo |
| P07-source_reconciled | Preparada / IDs | Completitud | Igualdad de conjunto de IDs y número de filas con raw | Critical | ExpectColumnValuesToBeInSet(True); no perder ni inventar registros |
| P07-year_integrity | Preparada / año | Consistencia | Igualdad con raw y [1900,2100] | Critical | ExpectColumnValuesToBeInSet(True); rango defensivo del contrato de este dataset |
| P07-category_integrity | Preparada / categoría | Consistencia | Igualdad con raw | Critical | ExpectColumnValuesToBeInSet(True) |
| P08 | Preparada / has_matches | Aptitud analítica | >=1 coincidencia | Critical | ExpectColumnValuesToBeInSet(True); sin coincidencias AR2/3 no son evaluables |
| P09 | Preparada / fully_matched | Cobertura | 100% elegibles vinculados | Warning | ExpectColumnValuesToBeInSet(True); visibiliza brecha, no fuerza enlaces falsos |

Critical bloquea y no reintenta. Warning conserva resultado y permite continuar bajo las políticas descritas. Por ello GX overall_success puede ser false mientras policy_accepted es true. Cualquier excepción del motor GX bloquea, incluso si la regla era Warning.

GX Core 1.8.1: contexto efímero aislado por tarea → fuente pandas → activo por capa → BatchDefinition whole_dataframe → ExpectationSuite → ValidationDefinition.run. Esta ejecución controlada equivale al checkpoint exigido: guarda resultado completo, suite, resumen y SHA256 antes de aplicar la política. No usa un booleano sin evidencia. Las columnas de control derivadas se calculan sobre una vista de validación y no corrigen el archivo preparado.
