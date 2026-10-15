import re
import unicodedata
import pandas as pd
from src.common import LOG, run_dir, write_json

ELIGIBLE = {'Record Of The Year','Best Pop Solo Performance','Best Rock Performance','Best R&B Performance','Best Rap Solo Performance','Best Female Pop Vocal Performance','Best Male Pop Vocal Performance'}
METRICS = ['popularity','energy','danceability']

def normalize(value):
    if pd.isna(value):
        return ''
    text = unicodedata.normalize('NFKC', str(value)).casefold()
    return re.sub(r'\s+',' ', ''.join(c if c.isalnum() else ' ' for c in text)).strip()

def integrate_frames(spotify, grammy):
    s = spotify.copy()
    g = grammy.copy()
    # A track may occur under several genres. Conflicting identity/measure records
    # cannot be resolved without an authoritative timestamp; exclude the whole ID.
    cols = ['artists','track_name'] + METRICS
    conflict = s.groupby('track_id')[cols].nunique(dropna=False).gt(1).any(axis=1)
    conflict_ids = set(conflict[conflict].index)
    missing = s[['track_id','artists','track_name']].isna().any(axis=1)
    rejected = s[s.track_id.isin(conflict_ids) | missing].copy()
    valid = s[~s.track_id.isin(conflict_ids) & ~missing].drop_duplicates('track_id').copy()
    index = {}
    by_id = valid.set_index('track_id').to_dict('index')
    for row in valid.itertuples():
        # Spotify documents multi-artist cells through their semicolon delimiter.
        for artist in str(row.artists).split(';'):
            key = (normalize(row.track_name), normalize(artist))
            if all(key):
                index.setdefault(key,set()).add(row.track_id)
    records = []
    for row in g.to_dict('records'):
        eligible = row['category'] in ELIGIBLE
        key = (normalize(row['nominee']),normalize(row['artist']))
        candidates = index.get(key,set()) if eligible and all(key) else set()
        status = 'out_of_scope' if not eligible else 'missing_key' if not all(key) else 'unmatched' if not candidates else 'ambiguous' if len(candidates)>1 else 'matched'
        tid = next(iter(candidates)) if status=='matched' else None
        track = by_id.get(tid,{})
        records.append({'source_row_id':int(row['source_row_id']), 'year':int(row['year']),
                        'category':row['category'], 'grammy_artist':row['artist'] or '[missing]',
                        'nominee':row['nominee'], 'eligible':eligible,'match_status':status,
                        'candidate_count':len(candidates),'track_id':tid,
                        'track_name':track.get('track_name'),'spotify_artists':track.get('artists'),
                        **{c:track.get(c) for c in METRICS}})
    out = pd.DataFrame(records)
    report = {'spotify_raw_rows':len(s),'spotify_unique_ids':int(s.track_id.nunique()),
              'conflicting_track_ids':len(conflict_ids),'quarantined_spotify_rows':len(rejected),
              'spotify_canonical_tracks':len(valid),'grammy_raw_rows':len(g),'prepared_rows':len(out),
              'status_counts':out.match_status.value_counts().to_dict(),
              'eligible_records':int(out.eligible.sum()),'matched_records':int(out.match_status.eq('matched').sum())}
    return out, rejected, report

def run(spotify_path, grammy_path, run_id):
    out, rejected, report = integrate_frames(pd.read_csv(spotify_path), pd.read_parquet(grammy_path))
    folder = run_dir(run_id)
    out.to_parquet(folder / 'prepared.parquet',index=False)
    rejected.to_parquet(folder / 'spotify_quarantine.parquet',index=False)
    write_json(folder / 'integration.json',report)
    LOG.info('run=%s integration=%s',run_id,report)
    return str(folder / 'prepared.parquet')
