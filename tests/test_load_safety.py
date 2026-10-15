import json
import os
import shutil
from pathlib import Path
import pandas as pd
import pytest
from src.common import ROOT, run_dir
from src.validation import QualityFailure

def accepted_batch():
    evidence=ROOT/'docs/evidence/A_success/airflow_states.json'
    if not evidence.exists():
        pytest.skip('Requires real successful pipeline evidence')
    run_id=json.loads(evidence.read_text())['dag_run']['run_id']
    path=run_dir(run_id)/'prepared.parquet'
    if not path.exists():
        pytest.skip('Requires retained local prepared batch')
    return path

def test_tampered_prepared_file_cannot_load(tmp_path):
    from src.load import run
    source=accepted_batch()
    shutil.copy2(source.parent/'prepared_policy.json',tmp_path/'prepared_policy.json')
    df=pd.read_parquet(source)
    df.loc[0,'nominee']='tampered'
    path=tmp_path/'prepared.parquet';df.to_parquet(path,index=False)
    with pytest.raises(QualityFailure,match='stale SHA256'):
        run(path,'test_tampered')

@pytest.mark.skipif(not os.environ.get('PGHOST'),reason='Requires project PostgreSQL')
def test_mid_load_failure_rolls_back_entire_snapshot(monkeypatch):
    import src.load as loader
    from scripts.run_reliability import snapshot
    source=accepted_batch()
    original_connect=loader.connect
    before=snapshot()
    class FaultConnection:
        def __enter__(self):
            self.conn=original_connect('music_dw')
            self.conn.__enter__()
            return self
        def __exit__(self,*args):
            return self.conn.__exit__(*args)
        def execute(self,sql,*args):
            if sql.lstrip().startswith('INSERT INTO dw.fact_grammy_record'):
                raise RuntimeError('Controlled failure after dimension inserts, before fact insert')
            return self.conn.execute(sql,*args)
        def cursor(self):
            return self.conn.cursor()
    monkeypatch.setattr(loader,'connect',lambda database:FaultConnection())
    with pytest.raises(RuntimeError,match='Controlled failure'):
        loader.run(source,'test_rollback')
    assert snapshot()==before
