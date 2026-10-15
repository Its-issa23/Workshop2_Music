"""Create a source-controlled Power BI project with PostgreSQL DirectQuery."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'powerbi'
BASE='https://developer.microsoft.com/json-schemas/fabric/'
def save(path,data):
    p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

save('Music.pbip',{'$schema':BASE+'pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'Music.Report'}}],'settings':{'enableAutoRecovery':True}})
save('Music.Report/definition.pbir',{'$schema':BASE+'item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../Music.SemanticModel'}}})
save('Music.SemanticModel/definition.pbism',{'$schema':BASE+'item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})

tables=[]
def table(name,view,columns,measures):
    tables.append({'name':name,'columns':[{'name':c,'dataType':t,'sourceColumn':c,'summarizeBy':'none'} for c,t in columns],
                   'measures':[{'name':n,'expression':e,'formatString':f} for n,e,f in measures],
                   'partitions':[{'name':name,'mode':'directQuery','source':{'type':'m','expression':['let','    Source = PostgreSQL.Database("localhost:5433", "music_dw", [CreateNavigationProperties=false]),',f'    View = Source{{[Schema="dw", Item="{view}"]}}[Data]','in','    View']}}]})
table('Cobertura','kpi_coverage',[('category_name','string'),('eligible_records','int64'),('matched_records','int64'),('coverage_pct','double')],[
    ('Cobertura','DIVIDE(SUM(Cobertura[matched_records]), SUM(Cobertura[eligible_records]))','0.00%'),
    ('Elegibles','SUM(Cobertura[eligible_records])','#,0'),('Vinculados','SUM(Cobertura[matched_records])','#,0')])
table('Popularidad','kpi_popularity',[('category_name','string'),('distinct_tracks','int64'),('mean_popularity','double')],[
    ('Popularidad media','SELECTEDVALUE(Popularidad[mean_popularity])','0.00'),
    ('Canciones por categoria','SELECTEDVALUE(Popularidad[distinct_tracks])','#,0')])
table('Audio','kpi_audio',[('decade','int64'),('distinct_tracks','int64'),('mean_energy','double'),('mean_danceability','double')],[
    ('Energia media','SELECTEDVALUE(Audio[mean_energy])','0.0000'),
    ('Bailabilidad media','SELECTEDVALUE(Audio[mean_danceability])','0.0000'),
    ('Canciones por decada','SELECTEDVALUE(Audio[distinct_tracks])','#,0')])
save('Music.SemanticModel/model.bim',{'name':'Music','compatibilityLevel':1567,'model':{'culture':'es-ES','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US','tables':tables,'annotations':[{'name':'PBI_QueryOrder','value':json.dumps([t['name'] for t in tables])}]}})
report='Music.Report/definition/'
save(report+'version.json',{'$schema':BASE+'item/report/definition/versionMetadata/1.0.0/schema.json','version':'4.0.0'})
save(report+'report.json',{'$schema':BASE+'item/report/definition/report/2.0.0/schema.json','themeCollection':{}})
save(report+'pages/pages.json',{'$schema':BASE+'item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':['AR1','AR2','AR3'],'activePageName':'AR1'})

def literal(v):
    return {'expr':{'Literal':{'Value':("'"+v.replace("'","''")+"'") if isinstance(v,str) else str(v).lower()}}}
def field(table,name,measure=False):
    return {'field':{('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':name}},'queryRef':table+'.'+name,'nativeQueryRef':name}
def visual(page,name,kind,title,roles,x,y,w,h):
    content={'$schema':BASE+'item/report/definition/visualContainer/2.0.0/schema.json','name':name,'position':{'x':x,'y':y,'z':0,'height':h,'width':w,'tabOrder':0},
             'visual':{'visualType':kind,'query':{'queryState':{k:{'projections':v} for k,v in roles.items()}},
                       'visualContainerObjects':{'title':[{'properties':{'show':literal(True),'text':literal(title),'fontSize':literal(15),'titleWrap':literal(True)}}]},'drillFilterOtherVisuals':True}}
    save(report+f'pages/{page}/visuals/{name}/visual.json',content)
def text(page,name,title,body,y=20,h=110):
    content={'$schema':BASE+'item/report/definition/visualContainer/2.0.0/schema.json','name':name,'position':{'x':35,'y':y,'z':0,'height':h,'width':1210,'tabOrder':0},
             'visual':{'visualType':'textbox','objects':{'general':[{'properties':{'paragraphs':[
                 {'textRuns':[{'value':title,'textStyle':{'fontSize':'25pt','fontWeight':'bold','color':'#143B48'}}]},
                 {'textRuns':[{'value':body,'textStyle':{'fontSize':'12pt','color':'#42606B'}}]}]}}]}}}
    save(report+f'pages/{page}/visuals/{name}/visual.json',content)

for page,label in [('AR1','01 · Cobertura del cruce'),('AR2','02 · Popularidad por categoria'),('AR3','03 · Perfil de audio')]:
    save(report+f'pages/{page}/page.json',{'$schema':BASE+'item/report/definition/page/2.0.0/schema.json','name':page,'displayName':label,'displayOption':'FitToPage','height':720,'width':1280})
text('AR1','header1','GRAMMY × SPOTIFY | Cobertura verificable','AR1 · Coincidencias únicas de título + artista. Los registros ambiguos no se fuerzan. Fuente: PostgreSQL / music_dw.')
for i,m in enumerate(['Elegibles','Vinculados','Cobertura']):
    visual('AR1','card'+str(i),'card',m,{'Values':[field('Cobertura',m,True)]},35+i*410,135,390,120)
visual('AR1','coverage','clusteredBarChart','Porcentaje vinculado por categoría',{'Category':[field('Cobertura','category_name')],'Y':[field('Cobertura','Cobertura',True)]},35,280,1210,350)
text('AR1','note1','Alcance de la muestra','Solo siete categorías de interpretaciones de canciones. El flag winner no distingue ganadores de nominados.',650,65)
text('AR2','header2','Popularidad de las canciones vinculadas','AR2 · Media por canción Spotify distinta dentro de cada categoría. La puntuación corresponde a la instantánea Spotify, no al año del premio.')
visual('AR2','popularity','clusteredBarChart','Popularidad media (0–100)',{'Category':[field('Popularidad','category_name')],'Y':[field('Popularidad','Popularidad media',True)]},35,150,780,470)
visual('AR2','sample','tableEx','Tamaño de muestra',{'Values':[field('Popularidad','category_name'),field('Popularidad','Canciones por categoria',True)]},840,150,405,470)
text('AR2','note2','Interpretación','Las categorías tienen coberturas y tamaños distintos. Esta comparación no demuestra un efecto causal del reconocimiento.',650,65)
text('AR3','header3','Energía y bailabilidad por década Grammy','AR3 · Canciones distintas dentro de cada década. El tiempo corresponde al registro Grammy; el audio se mide en la instantánea Spotify.')
visual('AR3','audio','scatterChart','Perfil medio de audio (escala 0–1)',{'Category':[field('Audio','decade')],'X':[field('Audio','Energia media',True)],'Y':[field('Audio','Bailabilidad media',True)],'Size':[field('Audio','Canciones por decada',True)]},35,150,780,470)
visual('AR3','audioTable','tableEx','Medidas por década',{'Values':[field('Audio','decade'),field('Audio','Energia media',True),field('Audio','Bailabilidad media',True),field('Audio','Canciones por decada',True)]},840,150,405,470)
text('AR3','note3','Lectura responsable','Las décadas con pocas canciones tienen estimaciones inestables. La ausencia de una década significa que no hubo coincidencias aceptadas.',650,65)
save('connection.pbids',{'version':'0.1','connections':[{'details':{'protocol':'postgresql','address':{'server':'localhost:5433','database':'music_dw'}},'options':{},'mode':'DirectQuery'}]})
print('Power BI project generated:',OUT/'Music.pbip')
