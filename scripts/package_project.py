"""Create a reproducible deliverable ZIP without secrets or runtime databases."""
from pathlib import Path
import json
import zipfile

root=Path(__file__).resolve().parents[1]
out=root/'deliverables'
out.mkdir(exist_ok=True)
folders=['src','dags','sql','scripts','tests','notebooks','docs','gx','powerbi','.github']
files=['README.md','Dockerfile','requirements.txt','docker-compose.yaml','.env.example','.gitignore','.dockerignore']
paths=[root/f for f in files]
for name in folders:
    paths.extend(p for p in (root/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.pbi' not in p.parts and 'powerbi_schemas' not in p.parts and p.suffix!='.pyc')
paths.extend([root/'sources/spotify_dataset.csv',root/'sources/the_grammy_awards.csv'])
target=out/'workshop-2-entrega.zip'
secrets=[]
if (root/'.env').exists():
    for line in (root/'.env').read_text().splitlines():
        if '=' in line:
            key,value=line.split('=',1)
            if any(token in key for token in ['PASSWORD','SECRET','KEY']) and value:
                secrets.append(value.encode())
for path in paths:
    data=path.read_bytes()
    if any(secret in data for secret in secrets):
        raise ValueError('Secret detected in deliverable file: '+str(path.relative_to(root)))
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(set(paths)):
        archive.write(path,Path('workshop-2')/path.relative_to(root))
with zipfile.ZipFile(target) as archive:
    assert not any(Path(n).name=='.env' or '/.pbi/' in n or '/data/' in n for n in archive.namelist())
    assert archive.testzip() is None
print(target)
print('files:',len(paths),'bytes:',target.stat().st_size)
