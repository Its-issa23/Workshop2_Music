# Guion de defensa · 8–10 minutos

1. **Problema (1 min):** integrar dos fuentes heterogéneas con calidad demostrable. Explicar AR1–AR3 y por qué ambas fuentes son necesarias.
2. **Evidencia de calidad (2 min):** 114000 filas no equivalen a 114000 canciones; 720 IDs contradictorios y winner constante. Justificar cuarentena, cobertura conservadora y ausencia de KPI de ganadores.
3. **Modelo e integración (2 min):** una fila por registro Grammy; dimensiones de año, categoría, artista y canción; título+artista exactos normalizados; ambiguos excluidos de métricas, no eliminados del universo de hechos.
4. **Demostración (3 min):** mostrar A verde; luego B con S03 fallida y load bloqueado; revisar JSON y logs; abrir reliability_summary.json para explicar que B no cambió el DW y C no duplicó datos.
5. **Producto analítico (1 min):** Power BI con DirectQuery al DW; cobertura global 20,50%; señalar tamaños de muestra y que el año Grammy no es fecha de las métricas Spotify.
6. **Cierre técnico (1 min):** transacción, rollback, clave natural, SHA256 del preparado, reintentos solo transitorios, pendientes de fuentes y mejora mediante ISRC/identificadores autoritativos.

Preguntas de defensa:

- ¿Por qué no unir solo por título? Hay versiones/homónimos; varios track_id se clasifican ambiguous.
- ¿Por qué GX puede tener success=false y el DAG continuar? Algunas expectativas son advertencias; el criterio de aceptación documentado exige cero Critical y cero excepciones del motor.
- ¿Qué ocurre si falla la carga a mitad? PostgreSQL revierte la transacción completa; conserva el snapshot anterior.
- ¿Por qué no reintentar un error de calidad? Repetir la misma entrada inválida produce la misma violación.
- ¿Por qué no usar SQLite? La guía exige PostgreSQL/MySQL; las bases de metadatos, fuente y DW son PostgreSQL.
- ¿Cuál es el sesgo principal? Solo 33 de 161 registros elegibles coinciden de manera conservadora; los resultados no representan todos los premios.
- ¿La conexión BI usa CSV? No: tres vistas SQL sobre la estrella dimensional music_dw.
