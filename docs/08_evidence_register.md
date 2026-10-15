# Registro de evidencias

| ID | Ejecución / tarea | Artefacto | Qué demuestra | Estado |
|---|---|---|---|---|
| E01 | Diseño | docs/01_requirements.md, docs/07_traceability.md | AR1–AR3 y cadena de decisiones | Completo |
| E02 | Perfilado | notebooks/data_profiling.ipynb; docs/evidence/profiling.json; notebook_profile.json | Estructura, nulos, duplicados, distribuciones, temporalidad y cruce | Ejecutado |
| E03 | Preparación fuente | docs/evidence/source_import.json | 4810 CSV = 4810 PostgreSQL; todos los valores iguales | Aprobado |
| E04 | A_success | docs/evidence/A_success/airflow_states.json | Siete tareas success con tiempos y tries reales | Aprobado |
| E05 | A raw/prepared | docs/evidence/A_success/*_gx.json, *_suite.json, *_policy.json | GX por Rule ID; política distingue Warning de Critical | Aprobado |
| E06 | Integración A | docs/evidence/A_success/integration.json | Conservación de 4810 registros y cardinalidad | Aprobado |
| E07 | Load A | docs/evidence/A_success/load.json | Commit y cantidad dimensional | Aprobado |
| E08 | B_critical_raw_failure | docs/evidence/B_critical_raw_failure/spotify_raw_policy.json | S03 falla con popularity=101 | Aprobado |
| E09 | B tareas/logs | docs/evidence/B_critical_raw_failure/airflow_states.json; task_logs/ | Gate failed, descendientes upstream_failed, sin retry | Aprobado |
| E10 | C_safe_rerun | docs/evidence/reliability_summary.json | Igualdad A/B/C de conteos, medidas y hash de hechos | Aprobado |
| E11 | Reglas de borde | docs/evidence/tests.xml | Duplicados, conflictos, ambigüedad, nulos y gates | Aprobado |
| E12 | Consultas DW | docs/evidence/dw_analytics.json | Tres productos analíticos calculados por PostgreSQL | Aprobado |
| E13 | Power BI definición | powerbi/Music.pbip; docs/evidence/powerbi_schema_validation.json | Tres páginas, vistas DW DirectQuery, JSON válido | Aprobado |
| E14 | Power BI renderizado | docs/evidence/powerbi_AR*.png | Valores y legibilidad en Desktop | Pendiente de autenticación local |
| E15 | Airflow Graph/Grid | docs/evidence/airflow_A.png, airflow_B.png | Evidencia visual complementaria obligatoria | Pendiente de sesión UI; estados/logs ya preservados |
| E16 | GitHub | URL del repositorio | Publicación del entregable versionado | Pendiente de destino y acceso |

Los estados pendientes no se sustituyen con capturas simuladas. El éxito del motor ETL está probado con ejecuciones reales, pero la entrega académica completa requiere E14–E16.

## Interpretación del fallo B

La extracción Spotify tiene éxito porque adquirir un archivo no valida su semántica. El gate raw detecta 101 fuera de [0,100], regla S03. `validate_spotify_raw` falla en el primer intento; la otra rama puede completar sus tareas. La convergencia `all_success` impide transformar; las tres tareas posteriores quedan upstream_failed. La carga anterior sigue disponible. Ejecutar nuevamente con el mismo valor inválido no lo resolvería, por eso no hay reintento de calidad.

## Capturas a completar

En Airflow, abrir el DAG y seleccionar `evidence_A_success_*`: Graph o Grid debe mostrar las siete tareas verdes. Luego seleccionar `evidence_B_critical_raw_failure_*`: mostrar validate_spotify_raw fallida y descendientes bloqueados. Abrir Logs del gate y acompañar la captura con S03 y el JSON. En Power BI, completar la conexión PostgreSQL y capturar las tres páginas con sus datos.
