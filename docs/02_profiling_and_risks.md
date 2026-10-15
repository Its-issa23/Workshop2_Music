# Perfilado y riesgos

Evidencia reproducible: `notebooks/data_profiling.ipynb` y `docs/evidence/profiling.json`. El notebook perfila Spotify CSV y Grammy desde PostgreSQL, además de reconciliar la preparación original. Los originales se montan como solo lectura.

| Evidencia observada | Riesgo | Requisito | Respuesta |
|---|---|---|---|
| Spotify: 114000 filas, 89741 track_id distintos | Conteo inflado al tratar fila-género como canción | AR1–3 | Canonicalizar por ID; no usar género arbitrariamente |
| 720 IDs tienen contradicciones en título, artistas o medidas | Elegir una fila produciría un KPI arbitrario | AR1–3 | Cuarentena de todas las filas de esos IDs |
| 1 fila carece de artista, título y álbum | Unión incompleta | AR1 | Advertencia y cuarentena Spotify |
| Duración mínima 0, una fila con duración cero | No puede interpretarse como audio normal | Fuera de alcance | Registrar; no usar duración en KPIs |
| Popularidad 0–100; energía 0–1; bailabilidad 0–0.985 | Valores fuera del dominio alteran medias | AR2/3 | Regla crítica de dominio y no nulos |
| Grammy: 4810 filas, años 1958–2019 | Snapshot no representa premios posteriores | AR1–3 | Etiquetar cobertura temporal del origen |
| 1840 artist ausentes, 6 nominee ausentes en CSV | No todos los registros son vinculables | AR1 | Estado missing_key; no completar artistas con workers |
| winner=True en las 4810 filas | No distingue ganadores de nominados | AR1–3 | Advertencia y exclusión del campo de los indicadores |
| published_at/updated_at son fechas editoriales | Confundir publicación del sitio con ceremonia | AR3 | Usar year original, sin inferir fechas de ceremonia |
| Títulos compartidos y múltiples grabaciones | Unión por título puede ser muchos-a-muchos | AR1–3 | Título + artista normalizados; si hay varios IDs, ambiguous |

Las tablas del notebook muestran frecuencias de categorías, diferencias de mayúsculas, claves candidatas, nulos, cuantiles, fechas parseables y años faltantes. La medición de cruce está en integration.json por ejecución. El perfilado conserva datos; la normalización ocurre en la transformación.
