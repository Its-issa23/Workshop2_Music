import hashlib
import json
import logging
import os
from pathlib import Path

ROOT = Path(os.environ.get('PROJECT_ROOT', Path(__file__).resolve().parents[1]))
LOG = logging.getLogger('music_pipeline')

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    return str(path)

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def run_dir(run_id):
    name = hashlib.sha256(run_id.encode()).hexdigest()[:24]
    path = ROOT / 'data' / 'runs' / name
    path.mkdir(parents=True, exist_ok=True)
    write_json(path / 'run.json', {'run_id': run_id})
    return path

def connect(database):
    import psycopg
    return psycopg.connect(host=os.environ.get('PGHOST', 'postgres'), port=os.environ.get('PGPORT', '5432'), dbname=database, user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'])
