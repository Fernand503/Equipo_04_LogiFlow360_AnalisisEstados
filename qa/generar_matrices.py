"""Regenera matrices desde el .mdj conservando los IDs de fila del informe.
Si se agregan o retiran transiciones, falla hasta actualizar el orden y el informe.
No requiere paquetes externos.
"""
from pathlib import Path
import json,csv
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent
p=json.loads((ROOT/'LogiFlow360_StateModels.mdj').read_text(encoding='utf8'))
order=json.loads((BASE/'orden_transiciones.json').read_text(encoding='utf8'))
def walk(o):
 if isinstance(o,dict):
  if '_id'in o:yield o
  for v in o.values():yield from walk(v)
 elif isinstance(o,list):
  for v in o:yield from walk(v)
all=list(walk(p));ix={o['_id']:o for o in all};sms=[o for o in all if o['_type']=='UMLStateMachine']
def machine(o):
 while o['_type']!='UMLStateMachine':o=ix[o['_parent']['$ref']]
 return o
def label(o):
 if o['_type']=='UMLFinalState':return 'Final'
 if o.get('kind')=='initial':return 'Initial'
 if o.get('kind')=='choice':
  choices=[x for x in walk(machine(o)['regions'])if x.get('kind')=='choice']
  return f'Choice C{choices.index(o)+1}'
 parent=ix.get(o.get('_parent',{}).get('$ref'))
 owner=ix.get(parent.get('_parent',{}).get('$ref'))if parent else None
 return(owner['name']+'::'if owner and owner['_type']=='UMLState'else'')+o['name']
rows=[];md=['# Matrices de transición LogiFlow 360','','Fuente semántica: `LogiFlow360_StateModels.mdj`. Hay 219 transiciones; cada identificador NN-TNN corresponde al orden del informe. `Compuesto::Subestado` indica anidación. La documentación procede del campo Documentation del modelo.','','La verificación es estructural y usa escenarios seleccionados; no demuestra todas las combinaciones de guardas ni integraciones reales.','']
for n,sm in enumerate(sms,1):
 entity=sm['name'].removeprefix('SM_');ts=[t for t in walk(sm['regions'])if t['_type']=='UMLTransition']
 assert set(order[entity])=={t['_id']for t in ts},'El modelo cambió: actualizar orden e informe de '+entity
 md +=[f'## {n:02} {entity}','','| ID | Estado origen | Evento | Guarda | Efecto | Estado destino | Tipo | Justificación |','|---|---|---|---|---|---|---|---|']
 for i,tid in enumerate(order[entity],1):
  t=ix[tid];r={'id':f'{n:02}-T{i:02}','entidad':entity,'origen':label(ix[t['source']['$ref']]),'evento':', '.join(x['name']for x in t.get('triggers',[]))or'—','guarda':'['+t['guard']+']'if t.get('guard')else'—','efecto':'/ '+'; '.join(x['name']for x in t.get('effects',[]))if t.get('effects')else'—','destino':label(ix[t['target']['$ref']]),'tipo':t.get('kind','external'),'justificacion':t.get('documentation','')}
  assert r['justificacion'],f'Documentation vacío en {tid}'
  rows.append(r);md.append('| '+' | '.join(str(r[k]).replace('|','\\|').replace('\n',' ')for k in ['id','origen','evento','guarda','efecto','destino','tipo','justificacion'])+' |')
 md.append('')
with(ROOT/'Matrices_QA_LogiFlow360.csv').open('w',encoding='utf-8-sig',newline='')as f:
 writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
(ROOT/'Matrices_QA_LogiFlow360.md').write_text('\n'.join(md).rstrip()+'\n',encoding='utf8')
print(f'{len(rows)} transiciones exportadas a CSV y Markdown')
