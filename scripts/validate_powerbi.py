"""Validate authored PBIR against Microsoft's public versioned schemas."""
import json
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen
from referencing import Registry, Resource
from jsonschema import Draft7Validator

root=Path(__file__).resolve().parents[1]
model_path=root/'powerbi/Music.SemanticModel/model.bim'
model_definition=json.loads(model_path.read_text(encoding='utf-8'))['model']
model_tables={table['name']:table for table in model_definition['tables']}
fact_name='fact_grammy_record'
dimensions={'dim_year':'year_key','dim_category':'category_key','dim_artist':'artist_key','dim_track':'track_key'}
if fact_name not in model_tables or not dimensions.keys() <= model_tables.keys():
    raise ValueError('Power BI semantic model must contain the fact and four dimensions')
if {'Cobertura','Popularidad','Audio'} & model_tables.keys():
    raise ValueError('Disconnected KPI view tables must not replace the star schema')
relationships=model_definition.get('relationships',[])
for dimension,key in dimensions.items():
    matches=[r for r in relationships if r.get('fromTable')==fact_name and r.get('fromColumn')==key
             and r.get('toTable')==dimension and r.get('toColumn')==key and r.get('isActive') is True
             and r.get('crossFilteringBehavior')=='oneDirection']
    if len(matches)!=1 or matches[0].get('fromCardinality')!='many' or matches[0].get('toCardinality')!='one':
        raise ValueError(f'Missing active many-to-one star relationship: {fact_name}.{key} -> {dimension}.{key}')
if len(relationships)!=len(dimensions):
    raise ValueError('Unexpected semantic-model relationships; expected one edge per dimension')
required_measures={'Elegibles','Vinculados','Cobertura','Popularidad media','Canciones por categoria',
                   'Energia media','Bailabilidad media','Canciones por decada'}
fact_measures={measure['name'] for measure in model_tables[fact_name].get('measures',[])}
if not required_measures <= fact_measures:
    raise ValueError(f'Missing fact-table measures: {sorted(required_measures-fact_measures)}')

report_entities=set()
def collect_entities(value):
    if isinstance(value,dict):
        source=value.get('SourceRef')
        if isinstance(source,dict) and isinstance(source.get('Entity'),str):
            report_entities.add(source['Entity'])
        for child in value.values():
            collect_entities(child)
    elif isinstance(value,list):
        for child in value:
            collect_entities(child)
for path in (root/'powerbi/Music.Report/definition/pages').rglob('visual.json'):
    collect_entities(json.loads(path.read_text(encoding='utf-8')))
if not report_entities <= model_tables.keys():
    raise ValueError(f'Report references tables absent from the star schema: {sorted(report_entities-model_tables.keys())}')
cache={}
def retrieve(uri):
    if uri not in cache:
        cache[uri]=json.load(urlopen(uri))
    return Resource.from_contents(cache[uri])
registry=Registry(retrieve=retrieve)
checked=[]
for path in (root/'powerbi').rglob('*'):
    if path.is_file() and path.suffix in ['.json','.pbip','.pbir','.pbism']:
        value=json.loads(path.read_text(encoding='utf-8'))
        if '$schema' in value:
            schema=retrieve(value['$schema']).contents
            Draft7Validator(schema,registry=registry).validate(value)
            checked.append(str(path.relative_to(root)))
(root/'docs/evidence/powerbi_schema_validation.json').write_text(json.dumps({
    'valid':True,'files':checked,'schema_sources':list(cache),
    'star_schema':{'fact':fact_name,'dimensions':dimensions,'active_many_to_one_relationships':len(relationships),
                   'report_tables':sorted(report_entities),'fact_measures':sorted(required_measures)}
},indent=2),encoding='utf-8')
print('Validated',len(checked),'Power BI definitions')
