import json
from pathlib import Path
import pandas as pd
from src.common import ROOT, LOG, connect, digest, write_json
from src.validation import QualityFailure

def run(path, run_id):
    path=Path(path)
    acceptance=json.loads((path.parent/'prepared_policy.json').read_text())
    if not acceptance['policy_accepted'] or acceptance['artifact_sha256']!=digest(path):
        raise QualityFailure('Prepared acceptance missing, rejected, or stale SHA256')
    df=pd.read_parquet(path)
    # One transaction replaces the current analytical snapshot. Readers see either
    # the previous committed snapshot or the new complete one; failures roll back.
    with connect('music_dw') as conn:
        conn.execute('SELECT pg_advisory_xact_lock(8192318)')
        conn.execute('TRUNCATE dw.fact_grammy_record, dw.dim_track, dw.dim_artist, dw.dim_category, dw.dim_year RESTART IDENTITY')
        conn.execute('CREATE TEMP TABLE stage (source_row_id bigint, year integer, category text, grammy_artist text, nominee text, eligible boolean, match_status text, candidate_count integer, track_id text, track_name text, spotify_artists text, popularity double precision, energy double precision, danceability double precision) ON COMMIT DROP')
        with conn.cursor().copy('COPY stage FROM STDIN') as cp:
            for row in df.itertuples(index=False,name=None):
                cp.write_row([None if pd.isna(x) else x for x in row])
        conn.execute('INSERT INTO dw.dim_year SELECT DISTINCT year, (year/10)*10 FROM stage ORDER BY year')
        conn.execute('INSERT INTO dw.dim_category(category_name) SELECT DISTINCT category FROM stage ORDER BY category')
        conn.execute('INSERT INTO dw.dim_artist(artist_name) SELECT DISTINCT grammy_artist FROM stage ORDER BY grammy_artist')
        conn.execute('INSERT INTO dw.dim_track(track_id,track_name,spotify_artists) SELECT DISTINCT track_id,track_name,spotify_artists FROM stage WHERE track_id IS NOT NULL ORDER BY track_id')
        conn.execute('''INSERT INTO dw.fact_grammy_record
          SELECT s.source_row_id,s.year,c.category_key,a.artist_key,t.track_key,s.nominee,s.eligible,s.match_status,s.candidate_count,s.popularity,s.energy,s.danceability
          FROM stage s JOIN dw.dim_category c ON c.category_name=s.category
          JOIN dw.dim_artist a ON a.artist_name=s.grammy_artist
          LEFT JOIN dw.dim_track t ON t.track_id=s.track_id''')
        counts=conn.execute("SELECT count(*),count(*) FILTER (WHERE match_status='matched') FROM dw.fact_grammy_record").fetchone()
        if counts[0]!=len(df):
            raise QualityFailure('Load row reconciliation failed')
        conn.execute('INSERT INTO dw.load_audit(run_id,source_rows,matched_rows,prepared_sha256) VALUES (%s,%s,%s,%s) ON CONFLICT(run_id) DO UPDATE SET loaded_at=now(), source_rows=excluded.source_rows,matched_rows=excluded.matched_rows,prepared_sha256=excluded.prepared_sha256',(run_id,*counts,digest(path)))
    report={'run_id':run_id,'fact_rows':counts[0],'matched_rows':counts[1],'prepared_sha256':digest(path),'strategy':'atomic snapshot replacement'}
    write_json(path.parent/'load.json',report)
    LOG.info('load committed %s',report)
    return report
