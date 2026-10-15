"""Read-only profiling. Does not clean or rewrite source records."""
import argparse
import pandas as pd
from src.common import ROOT, digest, write_json

def profile_frame(df):
    out = {'rows': len(df), 'columns': list(df.columns), 'dtypes': df.dtypes.astype(str).to_dict(),
           'missing_counts': df.isna().sum().to_dict(), 'missing_percent': (100 * df.isna().mean()).round(4).to_dict(),
           'exact_duplicates': int(df.duplicated().sum()), 'distinct': df.nunique().to_dict(),
           'numeric': df.select_dtypes(include='number').describe().to_dict(),
           'frequencies': {c: df[c].value_counts(dropna=False).head(12).to_dict() for c in df.select_dtypes(exclude='number').columns}}
    for c in ['published_at', 'updated_at']:
        if c in df:
            dt = pd.to_datetime(df[c], errors='coerce', utc=True)
            out[c] = {'invalid': int((df[c].notna() & dt.isna()).sum()), 'min': str(dt.min()), 'max': str(dt.max())}
    if 'year' in df:
        years = sorted(df.year.dropna().astype(int).unique().tolist())
        out['year_coverage'] = {'years': years, 'gaps': sorted(set(range(min(years), max(years)+1))-set(years))}
        key=['year','category','nominee','artist']
        out['duplicate_grammy_natural_key_rows']=int(df.duplicated(key).sum())
        out['blank_strings']={c:int(df[c].astype(str).str.strip().eq('').sum()) for c in df.columns}
    if 'track_id' in df:
        out['duplicate_track_id_rows'] = int(df.track_id.duplicated().sum())
        out['zero_duration'] = int(df.duration_ms.eq(0).sum())
        columns = ['artists', 'track_name', 'popularity', 'energy', 'danceability']
        out['conflicting_track_ids'] = int(df.groupby('track_id')[columns].nunique(dropna=False).gt(1).any(axis=1).sum())
    return out

def run():
    result = {}
    for name in ['spotify_dataset', 'the_grammy_awards']:
        path = ROOT / 'sources' / f'{name}.csv'
        result[name] = {'sha256': digest(path), **profile_frame(pd.read_csv(path))}
    write_json(ROOT / 'docs/evidence/profiling.json', result)
    return result

if __name__ == '__main__':
    run()
