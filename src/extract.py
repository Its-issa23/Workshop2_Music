import shutil
import pandas as pd
from src.common import ROOT, LOG, connect, digest, run_dir, write_json

def spotify(run_id, failure_mode=False):
    path = run_dir(run_id) / 'spotify_raw.csv'
    shutil.copyfile(ROOT / 'sources/spotify_dataset.csv', path)
    if failure_mode:
        # Controlled fault on an isolated batch copy. Originals remain untouched.
        df = pd.read_csv(path)
        df.loc[0,'popularity'] = 101
        df.to_csv(path,index=False)
    meta = {'path':str(path),'sha256':digest(path),'source':'CSV','fault_injected':failure_mode}
    write_json(path.with_suffix('.metadata.json'),meta)
    LOG.info('run=%s extracted Spotify %s',run_id,meta)
    return str(path)

def grammys(run_id):
    # The operational source is PostgreSQL, never the provided Grammy CSV.
    with connect('grammy_source') as conn:
        cursor = conn.execute('SELECT * FROM source.grammy_awards ORDER BY source_row_id')
        df = pd.DataFrame(cursor.fetchall(), columns=[c.name for c in cursor.description])
    path = run_dir(run_id) / 'grammy_raw.parquet'
    df.to_parquet(path,index=False)
    write_json(path.with_suffix('.metadata.json'), {'database':'grammy_source','table':'source.grammy_awards','query':'SELECT * FROM source.grammy_awards ORDER BY source_row_id','rows':len(df),'sha256':digest(path)})
    LOG.info('run=%s extracted Grammy database rows=%s',run_id,len(df))
    return str(path)
