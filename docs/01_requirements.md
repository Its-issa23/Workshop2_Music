# Alcance y requisitos analíticos

Especificación recibida: Workshop-2: Building a Reliable Batch Data Pipeline. El usuario la identifica como proyecto 1; se implementan los requisitos del documento adjunto.

Definidos antes del perfilado y del modelo. Producto: catálogo analítico de registros Grammy y atributos de la instantánea Spotify, con cobertura y ambigüedad visibles. No se infieren premios ganados, causalidad ni popularidad histórica. La columna winner debe evaluarse antes de usarse.

| ID | Pregunta / decisión | Datos requeridos y fuentes | KPI y visualización | Grano |
|---|---|---|---|---|
| AR1 | ¿Qué proporción de registros de categorías de canciones puede vincularse inequívocamente con Spotify? | Grammy: año, categoría, nominee, artist; Spotify: track_name, artists, track_id | Porcentaje vinculado; barras de cobertura por categoría | Registro Grammy elegible, agrupado por categoría |
| AR2 | ¿Qué categorías tienen canciones vinculadas con mayor popularidad en la instantánea? | Datos AR1 y Spotify popularity | Popularidad media; barras por categoría | Canción Spotify distinta dentro de categoría |
| AR3 | ¿Cómo varían energía y bailabilidad de canciones vinculadas según década del registro Grammy? | Datos AR1, Grammy year, Spotify energy/danceability | Energía media y bailabilidad media; dispersión por década | Canción Spotify distinta dentro de década |

Las tres preguntas necesitan ambos orígenes: Grammy aporta el contexto de reconocimiento y Spotify las identidades/medidas. AR1 evalúa cobertura del cruce, no cobertura de todo el catálogo musical.

Categorías elegibles: Record Of The Year, Best Pop Solo Performance, Best Rock Performance, Best R&B Performance, Best Rap Solo Performance, Best Female Pop Vocal Performance y Best Male Pop Vocal Performance. Lista conservadora de interpretaciones de canciones; excluye álbumes, artistas y créditos de composición. No pretende agotar todas las categorías históricas.

Secuencia de trabajo: requisitos → perfilado reproducible → riesgos → modelo dimensional → reglas GX → transformación → DAG → pruebas A/B/reejecución → BI.
