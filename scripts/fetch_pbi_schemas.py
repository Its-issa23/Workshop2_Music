"""Download Microsoft's public JSON schemas for offline PBIR validation."""
import json
from pathlib import Path
from urllib.request import urlopen

root=Path(__file__).resolve().parents[1]/'docs/powerbi_schemas'
root.mkdir(parents=True,exist_ok=True)
base='https://developer.microsoft.com/json-schemas/fabric/'
paths=['pbip/pbipProperties/1.0.0/schema.json','item/report/definitionProperties/2.0.0/schema.json','item/report/definition/versionMetadata/1.0.0/schema.json','item/report/definition/report/2.0.0/schema.json','item/report/definition/pagesMetadata/1.0.0/schema.json','item/report/definition/page/2.0.0/schema.json','item/report/definition/visualContainer/2.0.0/schema.json','item/semanticModel/definitionProperties/1.0.0/schema.json','item/report/definition/visualConfiguration/2.0.0/schema-embedded.json']
for path in paths:
    data=json.load(urlopen(base+path))
    name=path.split('/')[-3]
    if name=='definitionProperties': name=path.split('/')[1]+'Definition'
    (root/(name+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(name,'required:',data.get('required'),'properties:',list(data.get('properties',{})))
