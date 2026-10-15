CREATE SCHEMA IF NOT EXISTS source;
CREATE TABLE IF NOT EXISTS source.grammy_awards (
 source_row_id bigint PRIMARY KEY,
 year text, title text, published_at text, updated_at text, category text,
 nominee text, artist text, workers text, img text, winner text
);
COMMENT ON TABLE source.grammy_awards IS 'Original CSV values, no cleaning. source_row_id is 1-based CSV record ordinal.';
