# Contrato de transformación e integración

1. Conservar raw con SHA256 y metadatos. Grammy se extrae con SELECT desde `grammy_source.source.grammy_awards`.
2. Identificar IDs Spotify con discrepancias en artists, track_name, popularity, energy o danceability. Enviar todas sus filas a cuarentena: sin timestamp autoritativo no hay razón para elegir una.
3. Enviar filas sin identidad/título/artista a cuarentena. Colapsar únicamente repeticiones por track_id cuyas columnas analíticas son iguales. Las diferencias de género/álbum no alteran los indicadores elegidos y no se elige un género representativo.
4. Normalizar claves con Unicode NFKC, casefold, puntuación a espacio y espacios repetidos a uno. Conservar acentos y palabras como live/remaster; no hay fuzzy matching ni traducción.
5. Separar artists Spotify por `;`. Cada canción puede contribuir varios artistas a su índice. Mantener el crédito Grammy entero: no adivinar cómo dividir colaboraciones o workers.
6. Buscar `(nominee normalizado, artist normalizado)` contra `(track_name normalizado, artista Spotify normalizado)` solo en categorías elegibles.
7. Cero candidatos: unmatched; varios track_id: ambiguous; clave incompleta: missing_key; categoría excluida: out_of_scope. Solo exactamente un ID produce matched y métricas. Todos los registros Grammy llegan a la salida con estado explícito.
8. Convertir year a entero después de la validación raw. Conservar nominee y category originales; crédito ausente se representa [missing]. No usar published_at como año de premio ni winner como verdad de ganador.

Cardinalidad: los índices de búsqueda pueden devolver muchos candidatos, pero la salida tiene exactamente una fila por source_row_id. Relación hecho→canción muchos-a-uno opcional; una canción puede aparecer en varios años/categorías. P02 y P07 verifican que el cruce no multiplique ni pierda registros. Las consultas deduplican track_id dentro de cada grupo analítico.

Excepciones: conservar `spotify_quarantine.parquet`, estados de no coincidencia y reconciliation `integration.json`. No se cambia una fila para pasar GX. La cobertura es conservadora y tiene falsos negativos por versiones, créditos o acentos distintos. Una coincidencia textual no prueba identidad discográfica perfecta; no hay identificador común ISRC en ambas fuentes.

Impacto: AR1 usa todos los elegibles como denominador; AR2/3 solo matched. Los resultados describen la muestra vinculada y sus sesgos de cobertura. La década pertenece al registro Grammy, las métricas Spotify a una instantánea sin fecha de observación proporcionada.
