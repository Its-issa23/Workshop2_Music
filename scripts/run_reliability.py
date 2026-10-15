"""Run real scheduler tests A/B/C and export evidence from PostgreSQL metadata.
Usage: docker compose exec airflow python scripts/run_reliability.py
"""
import hashlib
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from src.common import ROOT, connect, run_dir, write_json

DAG='reliable_music_pipeline'

def query(db, sql, args=()):
    with connect(db) as conn:
        cur=conn.execute(sql,args)
        return [dict(zip([c.name for c in cur.description],row)) for row in cur.fetchall()]

def snapshot():
    rows=query('music_dw','''SELECT f.source_row_id,f.year_key,c.category_name,a.artist_name,t.track_id,f.nominee,f.eligible,f.match_status,f.candidate_count,f.popularity,f.energy,f.danceability
     FROM dw.fact_grammy_record f JOIN dw.dim_category c USING(category_key) JOIN dw.dim_artist a USING(artist_key) LEFT JOIN dw.dim_track t USING(track_key) ORDER BY f.source_row_id''')
    return {'rows':len(rows),'business_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest(),
            'measures':query('music_dw',"SELECT count(*) AS rows,count(*) FILTER (WHERE match_status='matched') AS matches,sum(popularity) AS popularity_sum,sum(energy) AS energy_sum,sum(danceability) AS danceability_sum FROM dw.fact_grammy_record")}

def run_one(label, fault=False):
    run_id=f'evidence_{label}_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")}'
    result=subprocess.run(['airflow','dags','trigger',DAG,'--run-id',run_id,'--conf',json.dumps({'inject_raw_failure':fault})],capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    deadline=time.time()+900
    while time.time()<deadline:
        records=query('airflow','SELECT run_id,state,start_date,end_date FROM dag_run WHERE dag_id=%s AND run_id=%s',(DAG,run_id))
        if records and records[0]['state'] in ['success','failed']:
            break
        time.sleep(5)
    else:
        raise TimeoutError(run_id)
    tasks=query('airflow','SELECT task_id,state,try_number,max_tries,start_date,end_date FROM task_instance WHERE dag_id=%s AND run_id=%s ORDER BY task_id',(DAG,run_id))
    folder=ROOT/'docs/evidence'/label
    folder.mkdir(parents=True,exist_ok=True)
    write_json(folder/'airflow_states.json',{'dag_run':records[0],'tasks':tasks})
    batch=run_dir(run_id)
    for file in batch.glob('*.json'):
        shutil.copy2(file,folder/file.name)
    # Preserve structured task logs, including the controlled failure explanation.
    log_root=ROOT/'logs'/f'dag_id={DAG}'/f'run_id={run_id}'
    if log_root.exists():
        shutil.copytree(log_root,folder/'task_logs',dirs_exist_ok=True)
    write_json(folder/'dw_snapshot.json',snapshot())
    expected='failed' if fault else 'success'
    assert records[0]['state']==expected, (label,records,tasks)
    if fault:
        states={t['task_id']:t['state'] for t in tasks}
        assert states['validate_spotify_raw']=='failed'
        assert all(states[t]=='upstream_failed' for t in ['transform_and_integrate','validate_prepared','load_dw'])
        assert next(t for t in tasks if t['task_id']=='validate_spotify_raw')['try_number']==1
    print(label,run_id,expected,flush=True)
    return snapshot()

def main():
    a=run_one('A_success')
    b=run_one('B_critical_raw_failure',True)
    c=run_one('C_safe_rerun')
    assert a==b==c, 'DW changed after rejected batch or identical-input rerun'
    write_json(ROOT/'docs/evidence/reliability_summary.json',{'A':a,'B':b,'C':c,'unchanged_after_failure':a==b,'safe_rerun':a==c})
    analytics={name:query('music_dw',f'SELECT * FROM dw.{name} ORDER BY 1') for name in ['kpi_coverage','kpi_popularity','kpi_audio']}
    write_json(ROOT/'docs/evidence/dw_analytics.json',analytics)
    print('A/B/C passed; evidence retained.',flush=True)

if __name__=='__main__':
    main()
