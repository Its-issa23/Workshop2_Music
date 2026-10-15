# Trazabilidad de extremo a extremo

| Requisito | Datos | Riesgo | Regla / Expectation | Transformación | DW | KPI / visual |
|---|---|---|---|---|---|---|
| AR1 | G.artist/nominee/category; S.artists/track_name/track_id | Identidad faltante o ambigua | S05 NotNull, S06 Unique; P02 Unique, P07 InSet | Normalización, cuarentena, candidatos únicos; conservar unmatched | Fact.match_status, eligible; dim_category | kpi_coverage; barras de cobertura |
| AR2 | G.category; S.track_id/popularity | Popularidad inválida y doble conteo por género | S03 Between(0,100), P05 Between, P02 Unique | Canonicalizar ID y deduplicar canción por categoría al consultar | Fact.popularity; dim_track/category | kpi_popularity; barras de popularidad media |
| AR3 | G.year; S.track_id/energy/danceability | Fecha editorial confundida con año de premio; audio inválido | G04 Regex, P07-year_integrity InSet; S04/P06 Between | Año original a entero; década; medidas de snapshot | dim_year; fact.energy/danceability | kpi_audio; dispersión energía/bailabilidad por década |

Todas las tablas, reglas y visualizaciones usan estos IDs. Las reglas de esquema, conteo, nulidad e integridad protegen el conjunto de los tres requisitos.
