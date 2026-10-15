# Power BI · Music

Abrir `Music.pbip` en Power BI Desktop. Formato PBIR editable y modelo TMSL `model.bim`, DirectQuery PostgreSQL; no se conectan los CSV originales.

Conexión: `localhost:5433`, base `music_dw`, usuario `POSTGRES_USER` y contraseña `POSTGRES_PASSWORD` de `.env` en la raíz del proyecto. Introducirlos en el diálogo de base de datos de Power BI. No añadirlos a los archivos del modelo ni subirlos a GitHub. Para un servidor diferente, editar las tres expresiones M de las particiones antes de abrir el proyecto.

| Página | Fuente DW | KPI | Visual |
|---|---|---|---|
| 01 · Cobertura | dw.kpi_coverage | SUM(matched_records) / SUM(eligible_records) | Tres tarjetas y barras por categoría |
| 02 · Popularidad | dw.kpi_popularity | Media por canción distinta/categoría | Barras y tabla de tamaño muestral |
| 03 · Audio | dw.kpi_audio | Medias de energía y bailabilidad por canción distinta/década | Dispersión y tabla |

El modelo consume vistas que consultan las tablas de la estrella. Cada vista ya tiene su grano analítico correcto. Las medidas de AR2/AR3 usan SELECTEDVALUE para no agregar promedios de grupos con distinto denominador; el total no se presenta como un promedio global. AR1 sí usa la razón de sumas y evita promediar porcentajes.

Valores de referencia verificados contra PostgreSQL: 161 elegibles, 33 vinculados, 20,50% cobertura. En Best Pop Solo Performance: 3 canciones, popularidad media 83,67. Década 2010: 12 canciones distintas, energía 0,6748 y bailabilidad 0,6104. Detalle: `docs/evidence/dw_analytics.json`.

Comprobación visual pendiente hasta completar la primera autenticación: verificar que las tres páginas muestran valores, que las categorías largas son legibles y que AR3 utiliza cada década como detalle. Guardar el PBIP o un PBIX local tras conectar. Capturas sugeridas: `docs/evidence/powerbi_AR1.png`, `powerbi_AR2.png`, `powerbi_AR3.png`.

Reconstrucción opcional: `python scripts/build_powerbi.py` reemplaza las definiciones por la versión base; no ejecutarlo después de ajustes manuales sin conservarlos. Validación JSON: `docker compose run --rm bootstrap python scripts/validate_powerbi.py` (solo valida, no ejecuta bootstrap porque se reemplaza su comando).
