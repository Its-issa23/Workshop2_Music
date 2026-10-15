"""GX suites, retained per-rule results and severity-aware blocking policy."""
from pathlib import Path
import json
import pandas as pd
import great_expectations as gx
from src.common import LOG, digest, write_json

class QualityFailure(ValueError):
    pass

def make_rules(layer, df):
    rules = []
    def add(rule_id, expectation, severity='Critical', **kwargs):
        rules.append(getattr(gx.expectations,expectation)(**kwargs, meta={'rule_id':rule_id,'severity':severity,'requirements':['AR1','AR2','AR3']}))
    add(layer+'-COUNT','ExpectTableRowCountToBeBetween',min_value=1)
    if layer=='spotify_raw':
        add('S01','ExpectTableColumnsToMatchSet',column_set=['track_id','track_name','artists','popularity','energy','danceability'],exact_match=False)
        for c in ['track_id','popularity','energy','danceability']:
            add('S02-'+c,'ExpectColumnValuesToNotBeNull',column=c)
        add('S03','ExpectColumnValuesToBeBetween',column='popularity',min_value=0,max_value=100)
        for c in ['energy','danceability']:
            add('S04-'+c,'ExpectColumnValuesToBeBetween',column=c,min_value=0,max_value=1)
        for c in ['artists','track_name']:
            add('S05-'+c,'ExpectColumnValuesToNotBeNull',severity='Warning',column=c)
        add('S06','ExpectColumnValuesToBeUnique',severity='Warning',column='track_id')
    elif layer=='grammy_raw':
        add('G01','ExpectTableColumnsToMatchSet',column_set=['source_row_id','year','category','nominee','artist','winner'],exact_match=False)
        add('G02','ExpectColumnValuesToBeUnique',column='source_row_id')
        for c in ['source_row_id','year','category']:
            add('G03-'+c,'ExpectColumnValuesToNotBeNull',column=c)
        add('G04','ExpectColumnValuesToMatchRegex',column='year',regex=r'^\d{4}$')
        add('G05','ExpectColumnValuesToNotMatchRegex',column='category',regex=r'^\s*$')
        add('G06','ExpectColumnValuesToNotMatchRegex',severity='Warning',column='artist',regex=r'^\s*$')
        add('G07','ExpectColumnUniqueValueCountToBeBetween',severity='Warning',column='winner',min_value=2)
    else:
        columns=['source_row_id','year','category','grammy_artist','nominee','eligible','match_status','candidate_count','track_id','track_name','spotify_artists','popularity','energy','danceability']
        add('P01','ExpectTableColumnsToMatchSet',column_set=columns,exact_match=False)
        add('P02','ExpectColumnValuesToBeUnique',column='source_row_id')
        for c in ['source_row_id','year','category','grammy_artist','eligible','match_status','candidate_count']:
            add('P03-'+c,'ExpectColumnValuesToNotBeNull',column=c)
        add('P04','ExpectColumnValuesToBeInSet',column='match_status',value_set=['matched','unmatched','ambiguous','missing_key','out_of_scope'])
        add('P05','ExpectColumnValuesToBeBetween',column='popularity',min_value=0,max_value=100)
        for c in ['energy','danceability']:
            add('P06-'+c,'ExpectColumnValuesToBeBetween',column=c,min_value=0,max_value=1)
        for c in ['match_integrity','source_reconciled','year_integrity','category_integrity']:
            add('P07-'+c,'ExpectColumnValuesToBeInSet',column=c,value_set=[True])
        add('P08','ExpectColumnValuesToBeInSet',column='has_matches',value_set=[True])
        add('P09','ExpectColumnValuesToBeInSet',severity='Warning',column='fully_matched',value_set=[True])
    return rules

def prepared_view(df, raw):
    """Computed audit columns only; source and prepared artifacts stay unchanged."""
    from src.transform import ELIGIBLE
    view=df.copy()
    matched=view.match_status.eq('matched')
    measures=['popularity','energy','danceability']
    present=view[['track_id','track_name','spotify_artists']+measures].notna().all(axis=1)
    empty=view[['track_id','track_name','spotify_artists']+measures].isna().all(axis=1)
    expected_eligible=view.category.isin(ELIGIBLE)
    valid_status=((view.match_status.eq('matched') & view.candidate_count.eq(1)) |
                  (view.match_status.eq('ambiguous') & view.candidate_count.gt(1)) |
                  (view.match_status.isin(['unmatched','missing_key','out_of_scope']) & view.candidate_count.eq(0)))
    view['match_integrity']=((matched & present) | (~matched & empty)) & valid_status & view.eligible.eq(expected_eligible) & view.match_status.eq('out_of_scope').eq(~expected_eligible)
    view['source_reconciled']=len(view)==len(raw) and set(view.source_row_id)==set(raw.source_row_id)
    source=raw.set_index('source_row_id')
    view['year_integrity']=view.year.eq(view.source_row_id.map(pd.to_numeric(source.year,errors='coerce'))) & view.year.between(1900,2100)
    view['category_integrity']=view.category.eq(view.source_row_id.map(source.category))
    view['has_matches']=bool(matched.any())
    view['fully_matched']=~view.eligible | matched
    return view

def run(path, layer):
    path=Path(path)
    df=pd.read_csv(path) if path.suffix=='.csv' else pd.read_parquet(path)
    if layer=='prepared':
        df=prepared_view(df,pd.read_parquet(path.parent/'grammy_raw.parquet'))
    context=gx.get_context(mode='ephemeral')
    ds=context.data_sources.add_pandas(name=layer)
    asset=ds.add_dataframe_asset(name=layer+'_asset')
    batch=asset.add_batch_definition_whole_dataframe('whole_batch')
    suite=context.suites.add(gx.ExpectationSuite(name=layer+'_suite'))
    for rule in make_rules(layer,df):
        suite.add_expectation(rule)
    definition=context.validation_definitions.add(gx.ValidationDefinition(name=layer+'_validation',data=batch,suite=suite))
    result=definition.run(batch_parameters={'dataframe':df},result_format={'result_format':'SUMMARY','partial_unexpected_count':10})
    payload=result.to_json_dict()
    write_json(path.parent/(layer+'_gx.json'),payload)
    summary=[]
    for item in payload['results']:
        meta=item['expectation_config']['meta']
        summary.append({'rule_id':meta['rule_id'],'severity':meta['severity'],'success':item['success'],'expectation':item['expectation_config']['type'],'result':item.get('result'),'exception_info':item.get('exception_info')})
    blocked=[r['rule_id'] for r in summary if not r['success'] and r['severity']=='Critical']
    # Any engine exception is a blocking validation failure, even on a warning rule.
    errors=[r['rule_id'] for r in summary if r.get('exception_info',{}).get('raised_exception')]
    report={'layer':layer,'artifact_sha256':digest(path),'gx_success':payload['success'],'policy_accepted':not(blocked or errors),'critical_failures':blocked,'engine_errors':errors,'rules':summary}
    write_json(path.parent/(layer+'_policy.json'),report)
    write_json(path.parent/(layer+'_suite.json'),suite.to_json_dict())
    LOG.info('validation layer=%s accepted=%s critical=%s warnings=%s',layer,report['policy_accepted'],blocked,[r['rule_id'] for r in summary if not r['success'] and r['severity']=='Warning'])
    if blocked or errors:
        raise QualityFailure(f'{layer}: Critical rules={blocked}, engine errors={errors}; evidence={path.parent / (layer+"_gx.json")}')
    return str(path)
