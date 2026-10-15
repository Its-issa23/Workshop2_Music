"""One-time operational source preparation; never called by the ETL DAG."""
import csv
from src.common import ROOT, connect, digest, write_json

def run():
    path = ROOT / 'sources/the_grammy_awards.csv'
    with path.open(encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ['year','title','published_at','updated_at','category','nominee','artist','workers','img','winner']
        rows = list(reader)
    with connect('grammy_source') as conn:
        conn.execute((ROOT / 'sql/source_setup.sql').read_text())
        conn.execute('TRUNCATE source.grammy_awards')
        with conn.cursor().copy('COPY source.grammy_awards FROM STDIN') as cp:
            for i,row in enumerate(rows,1):
                cp.write_row([i]+row)
        count = conn.execute('SELECT count(*) FROM source.grammy_awards').fetchone()[0]
        assert count == len(rows)
        # Compare every value, including empty strings, against source preparation.
        actual = conn.execute('SELECT * FROM source.grammy_awards ORDER BY source_row_id').fetchall()
        assert actual == [tuple([i]+row) for i,row in enumerate(rows,1)]
    with connect('music_dw') as conn:
        conn.execute((ROOT / 'sql/dw_schema.sql').read_text())
    write_json(ROOT / 'docs/evidence/source_import.json', {'source_sha256':digest(path),'csv_rows':len(rows),'database_rows':count,'all_values_equal':True,'database':'grammy_source','table':'source.grammy_awards'})

if __name__ == '__main__':
    run()
