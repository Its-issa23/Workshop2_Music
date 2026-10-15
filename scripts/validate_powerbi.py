"""Validate authored PBIR against Microsoft's public versioned schemas."""
import json
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen
from referencing import Registry, Resource
from jsonschema import Draft7Validator

root=Path(__file__).resolve().parents[1]
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
(root/'docs/evidence/powerbi_schema_validation.json').write_text(json.dumps({'valid':True,'files':checked,'schema_sources':list(cache)},indent=2),encoding='utf-8')
print('Validated',len(checked),'Power BI definitions')
