import pandas as pd
import pytest
from src.transform import integrate_frames, normalize
from src.validation import run, QualityFailure

def frames():
    s=pd.DataFrame([{'track_id':'a','artists':'Artist','track_name':'Song','popularity':50,'energy':.5,'danceability':.7},
                    {'track_id':'a','artists':'Artist','track_name':'Song','popularity':50,'energy':.5,'danceability':.7}])
    g=pd.DataFrame([{'source_row_id':1,'year':'2019','category':'Record Of The Year','nominee':'Song','artist':'Artist','winner':'True'}])
    return s,g

def test_genre_duplicates_do_not_multiply_fact_rows():
    s,g=frames()
    out,_,report=integrate_frames(s,g)
    assert len(out)==1 and out.iloc[0].track_id=='a'
    assert report['spotify_canonical_tracks']==1

def test_distinct_recordings_are_ambiguous():
    s,g=frames(); s.loc[1,'track_id']='b'
    out,_,_=integrate_frames(s,g)
    assert out.iloc[0].match_status=='ambiguous'
    assert out.iloc[0].candidate_count==2
    assert out.iloc[0].popularity is None

def test_conflicting_id_is_quarantined():
    s,g=frames(); s.loc[1,'popularity']=99
    out,rejected,_=integrate_frames(s,g)
    assert len(rejected)==2 and out.iloc[0].match_status=='unmatched'

def test_missing_artist_does_not_match_on_title_only():
    s,g=frames(); g.loc[0,'artist']=''
    out,_,_=integrate_frames(s,g)
    assert out.iloc[0].match_status=='missing_key'

def test_normalization_preserves_version_words_and_accents():
    assert normalize(' Song — Live ')== 'song live'
    assert normalize('Beyoncé') != normalize('Beyonce')

def test_raw_critical_failure_retains_evidence(tmp_path):
    s,_=frames(); s.loc[0,'popularity']=101
    path=tmp_path/'spotify.csv'; s.to_csv(path,index=False)
    with pytest.raises(QualityFailure,match='S03'):
        run(path,'spotify_raw')
    assert (tmp_path/'spotify_raw_gx.json').exists()

def test_warning_duplicate_allows_processing(tmp_path):
    s,_=frames(); path=tmp_path/'spotify.csv'; s.to_csv(path,index=False)
    assert run(path,'spotify_raw')==str(path)

def test_prepared_gate_rejects_lost_source_rows(tmp_path):
    s,g=frames(); out,_,_=integrate_frames(s,g)
    g=pd.concat([g,g.assign(source_row_id=2)],ignore_index=True)
    g.to_parquet(tmp_path/'grammy_raw.parquet',index=False)
    path=tmp_path/'prepared.parquet'; out.to_parquet(path,index=False)
    with pytest.raises(QualityFailure,match='P07-source_reconciled'):
        run(path,'prepared')
