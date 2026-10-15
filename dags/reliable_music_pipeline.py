from datetime import datetime, timedelta, timezone
from airflow.sdk import dag, task, get_current_context
from airflow.exceptions import AirflowFailException

def fail_fast(fn, *args):
    from src.validation import QualityFailure
    import psycopg
    try:
        return fn(*args)
    except (QualityFailure, ValueError, KeyError, FileNotFoundError) as error:
        raise AirflowFailException(str(error)) from error
    except psycopg.Error as error:
        if isinstance(error, (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.DeadlockDetected, psycopg.errors.SerializationFailure)):
            raise
        raise AirflowFailException(str(error)) from error

@dag(dag_id='reliable_music_pipeline',schedule=None,start_date=datetime(2025,1,1,tzinfo=timezone.utc),catchup=False,max_active_runs=1,tags=['workshop-2','music','quality'],default_args={'retries':0})
def reliable_music_pipeline():
    @task(retries=0)
    def extract_spotify():
        from src.extract import spotify
        ctx=get_current_context()
        conf=ctx['dag_run'].conf or {}
        return fail_fast(spotify,ctx['run_id'],conf.get('inject_raw_failure') is True)

    @task(retries=2,retry_delay=timedelta(seconds=20),retry_exponential_backoff=True)
    def extract_grammys():
        from src.extract import grammys
        return fail_fast(grammys,get_current_context()['run_id'])

    @task(retries=0)
    def validate_spotify_raw(path):
        from src.validation import run
        return fail_fast(run,path,'spotify_raw')

    @task(retries=0)
    def validate_grammys_raw(path):
        from src.validation import run
        return fail_fast(run,path,'grammy_raw')

    @task(retries=0)
    def transform_and_integrate(spotify_path,grammy_path):
        from src.transform import run
        return fail_fast(run,spotify_path,grammy_path,get_current_context()['run_id'])

    @task(retries=0)
    def validate_prepared(path):
        from src.validation import run
        return fail_fast(run,path,'prepared')

    @task(retries=2,retry_delay=timedelta(seconds=20),retry_exponential_backoff=True)
    def load_dw(path):
        from src.load import run
        return fail_fast(run,path,get_current_context()['run_id'])

    s=validate_spotify_raw(extract_spotify())
    g=validate_grammys_raw(extract_grammys())
    load_dw(validate_prepared(transform_and_integrate(s,g)))

reliable_music_pipeline()
