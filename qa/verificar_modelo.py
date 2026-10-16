"""Verificación estática y simulaciones acotadas del modelo, sin dependencias externas.

No sustituye al motor ni al renderizador de StarUML. Las simulaciones usan datos
de ejemplo y efectos locales mínimos; no llaman bancos, sensores ni servicios.
"""
from pathlib import Path
import json, re, ast, collections, itertools, datetime

BASE=Path(__file__).resolve().parent
MODEL=BASE.parent/'LogiFlow360_StateModels.mdj'
P=json.loads(MODEL.read_text(encoding='utf-8'))
def walk(v):
 if isinstance(v,dict):
  if '_id' in v:yield v
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
ALL=list(walk(P));IX={x['_id']:x for x in ALL};ERRORS=[];CHECKS=[]
def check(name,condition,detail=''):
 CHECKS.append({'check':name,'passed':bool(condition),'detail':detail})
 if not condition:ERRORS.append(name+': '+detail)
def refs(v):
 if isinstance(v,dict):
  if '$ref' in v:yield v['$ref']
  for x in v.values():yield from refs(x)
 elif isinstance(v,list):
  for x in v:yield from refs(x)
def ancestors(x):
 out=[]
 while x.get('_parent'):
  x=IX[x['_parent']['$ref']];out.append(x)
 return out
def name(x):return x.get('name') or x.get('kind') or x['_type']
def trigger(t):return ', '.join(x['name'] for x in t.get('triggers',[]))
def guard(g,ctx):
 if not g:return True
 if g=='else':return False
 expression=re.sub(r'!(?!=)',' not ',g.replace('&&',' and ').replace('||',' or ')).strip()
 tree=ast.parse(expression,mode='eval')
 allowed=(ast.Expression,ast.BoolOp,ast.UnaryOp,ast.Compare,ast.Name,ast.Load,ast.Constant,ast.And,ast.Or,ast.Not,ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE)
 if any(not isinstance(n,allowed) for n in ast.walk(tree)):raise ValueError('Guarda fuera del subconjunto de simulación: '+g)
 return bool(eval(compile(tree,'<guard>','eval'),{'__builtins__':{}},ctx))

check('Identificadores únicos',len(ALL)==len(IX))
missing=set(refs(P))-IX.keys();check('Referencias resueltas',not missing,str(sorted(missing)))
def parent_errors(v,parent=None):
 out=[]
 if isinstance(v,dict):
  if '_id' in v:
   if parent and v.get('_parent',{}).get('$ref')!=parent['_id']:out.append((v['_id'],v.get('_parent'),parent['_id']))
   parent=v
  for value in v.values():out+=parent_errors(value,parent)
 elif isinstance(v,list):
  for value in v:out+=parent_errors(value,parent)
 return out
check('Propiedad y contención consistentes',not parent_errors(P),str(parent_errors(P)[:3]))
SMS=[x for x in ALL if x['_type']=='UMLStateMachine']
check('Diez máquinas y diez diagramas',len(SMS)==10 and sum(x['_type']=='UMLStatechartDiagram' for x in ALL)==10)
summary=[]
for sm in SMS:
 nodes=[x for x in walk(sm['regions']) if x['_type'] in ('UMLState','UMLFinalState','UMLPseudostate')]
 ts=[x for x in walk(sm['regions']) if x['_type']=='UMLTransition'];ids={x['_id'] for x in nodes}
 initial=[s for s in nodes if s.get('kind')=='initial'];check(sm['name']+': un Initial',len(initial)==1)
 for s in initial:
  out=[t for t in ts if t['source']['$ref']==s['_id']]
  check(sm['name']+': inicio sin trigger ni guarda',len(out)==1 and not out[0].get('triggers') and not out[0].get('guard'))
 for s in nodes:
  outgoing=[t for t in ts if t['source']['$ref']==s['_id']]
  if s['_type']=='UMLFinalState':check(sm['name']+': Final sin salidas '+s['_id'],not outgoing)
  elif s.get('kind')=='choice':check(sm['name']+': Choice bien formado '+s['_id'],len(outgoing)>=2 and all(t.get('guard') and not t.get('triggers') for t in outgoing))
  else:
   inherited=[t for t in ts if any(a['_id']==t['source']['$ref'] for a in ancestors(s) if a['_type']=='UMLState')]
   check(sm['name']+': salida de '+name(s),bool(outgoing or inherited))
 # Alcanzabilidad topológica: activar un subestado activa sus estados contenedores.
 reach={s['_id'] for s in initial}
 while True:
  before=set(reach)
  for nid in list(reach):reach.update(a['_id'] for a in ancestors(IX[nid]) if a['_type']=='UMLState')
  for t in ts:
   if t['source']['$ref'] in reach:reach.add(t['target']['$ref'])
  if before==reach:break
 check(sm['name']+': todos los vértices alcanzables',ids<=reach,str([name(IX[i]) for i in ids-reach]))
 diagram=next(x for x in sm['ownedElements'] if x['_type']=='UMLStatechartDiagram')
 nv={v['model']['$ref']:v for v in diagram['ownedViews'] if v['_type'] in ('UMLStateView','UMLPseudostateView','UMLFinalStateView')}
 ev={v['model']['$ref']:v for v in diagram['ownedViews'] if v['_type']=='UMLTransitionView'}
 check(sm['name']+': un dibujo por vértice y transición',set(nv)==ids and set(ev)=={t['_id'] for t in ts})
 check(sm['name']+': extremos gráficos correctos',all(IX[ev[t['_id']]['tail']['$ref']]['model']['$ref']==t['source']['$ref'] and IX[ev[t['_id']]['head']['$ref']]['model']['$ref']==t['target']['$ref'] for t in ts))
 summary.append({'entity':sm['name'].removeprefix('SM_'),'vertices':len(nodes),'states':sum(x['_type']=='UMLState' for x in nodes),'transitions':len(ts),'composites':sum(bool(x.get('regions')) for x in nodes),'after':sum(any(e['name'].startswith('after(') for e in t.get('triggers',[])) for t in ts),'choices':sum(x.get('kind')=='choice' for x in nodes)})
check('Compuestos en al menos dos diagramas',sum(s['composites']>0 for s in summary)>=2)
check('after() en al menos cuatro diagramas',sum(s['after']>0 for s in summary)>=4)
check('Choice en al menos tres diagramas',sum(s['choices']>0 for s in summary)>=3)
check('Acciones internas en al menos cinco entidades',sum(any(x.get('entryActivities') or x.get('doActivities') or x.get('exitActivities') for x in walk(sm['regions']) if x['_type']=='UMLState') for sm in SMS)>=5)

class Invalid(Exception):pass
class Sim:
 def __init__(self,entity,state,**ctx):
  self.sm=next(s for s in SMS if s['name']=='SM_'+entity)
  self.ns=[x for x in walk(self.sm['regions']) if x['_type'] in ('UMLState','UMLFinalState','UMLPseudostate')]
  self.ts=[x for x in walk(self.sm['regions']) if x['_type']=='UMLTransition']
  self.s=next(n for n in self.ns if n.get('name')==state);self.ctx=ctx;self.path=[state]
 def effects(self,t):
  for effect in t.get('effects',[]):
   n=effect['name']
   if n=='incrementarIntentosTotales()':self.ctx['intentosTotales']+=1
   if n=='incrementarIntentosEntrega()':self.ctx['intentosEntrega']+=1
   if n=='descontarStockAtomico()':self.ctx['existencias']-=self.ctx['cantidad']
   if n=='marcarServicioParaRegreso()':self.ctx['servicioPendiente']=True
   if n=='registrarAutorizacion()':self.ctx['pagoAutorizado']=True
 def select(self,ts):
  matches=[t for t in ts if t.get('guard')!='else' and guard(t.get('guard',''),self.ctx)]
  if not matches:matches=[t for t in ts if t.get('guard')=='else']
  if len(matches)>1:raise AssertionError('Guardas solapadas: '+name(self.s))
  return matches[0] if matches else None
 def take(self,t):
  self.effects(t)
  if t.get('kind')!='internal':self.s=IX[t['target']['$ref']];self.path.append(name(self.s))
 def settle(self):
  for _ in range(30):
   if self.s['_type']=='UMLFinalState':return
   if self.s.get('doActivities'):return
   ts=[t for t in self.ts if t['source']['$ref']==self.s['_id'] and not t.get('triggers')]
   t=self.select(ts)
   if not t:return
   self.take(t)
  raise AssertionError('Posible ciclo de finalización')
 def fire(self,tr):
  for s in [self.s]+[a for a in ancestors(self.s) if a['_type']=='UMLState']:
   ts=[t for t in self.ts if t['source']['$ref']==s['_id'] and trigger(t)==tr]
   t=self.select(ts)
   if t:self.take(t);self.settle();return self
  raise Invalid(name(self.s)+' no permite '+tr)
 def at(self,state):return self.s.get('name')==state

def scenario(title,fn):
 try:fn();check('Escenario: '+title,True)
 except Exception as ex:check('Escenario: '+title,False,type(ex).__name__+': '+str(ex))
def expect(condition):
 if not condition:raise AssertionError('Resultado inesperado')
def rejected(s,tr):
 before=s.s['_id']
 try:s.fire(tr)
 except Invalid:expect(s.s['_id']==before);return
 raise AssertionError('Se aceptó un evento inválido')

def payment_three():
 s=Sim('TransaccionDePago','En_Analisis_Antifraude',scoringValido=True,riesgo=10,umbralRiesgo=50,intentosTotales=0,firmaValida=True,correlacionValida=True,resultado='INSUFFICIENT_FUNDS',resultadoPrevioConfirmado=True)
 s.fire('recibirScoring()')
 for i in range(3):
  s.fire('recibirRespuesta()')
  if i<2:s.fire('reintentarPago()')
 expect(s.ctx['intentosTotales']==3 and 'Fallida_Definitiva' in s.path)
 rejected(s,'reintentarPago()')
scenario('pago: tres envíos y rechazo del cuarto',payment_three)
def payment_unknown():
 s=Sim('TransaccionDePago','Esperando_Respuesta_Pasarela',intentosTotales=1,firmaValida=True,correlacionValida=True,resultado='APPROVED')
 s.fire('after(timeoutPasarela)');expect(s.at('En_Conciliacion'));s.fire('confirmarResultadoConciliado()')
 expect(s.at('Autorizada') and s.ctx['intentosTotales']==1)
scenario('pago: timeout se concilia sin nuevo intento',payment_unknown)
def payment_threshold():
 s=Sim('TransaccionDePago','En_Analisis_Antifraude',scoringValido=True,riesgo=50,umbralRiesgo=50,intentosTotales=0)
 s.fire('recibirScoring()');expect('Rechazada_Por_Riesgo' in s.path and s.ctx['intentosTotales']==0)
scenario('pago: umbral exacto rechaza por riesgo',payment_threshold)
def payment_3ds():
 s=Sim('TransaccionDePago','Esperando_Respuesta_Pasarela',firmaValida=True,correlacionValida=True,resultado='REQUIRES_3DS',resultado3DS='APPROVED',intentosTotales=1)
 s.fire('recibirRespuesta()');expect(s.at('En_Desafio_3D_Secure'));s.fire('recibirResultado3DS()');expect(s.at('Autorizada') and s.ctx['intentosTotales']==1)
scenario('pago: 3DS no crea otro cargo',payment_3ds)
def order_cancel():
 s=Sim('OrdenDeCompra','En_Procesamiento_Almacen',actorAutorizado=True,stockDisponible=True,cancelacionConfirmada=False)
 s.fire('cancelarOrden()');expect('Cancelada_Por_Usuario' in s.path);rejected(s,'confirmarEmpaque()')
scenario('orden: cancelar impide empaquetar después',order_cancel)
scenario('orden: cancelar después de empaque se rechaza',lambda:rejected(Sim('OrdenDeCompra','Empacada',actorAutorizado=True),'cancelarOrden()'))
def order_timeout():
 s=Sim('OrdenDeCompra','Esperando_Autorizacion_Pago',pagoAutorizado=False)
 s.fire('after(30 min)');expect('Cancelada_Por_Timeout' in s.path);rejected(s,'confirmarPago()')
scenario('orden: timeout no revive por pago tardío',order_timeout)
def stock_expired():
 s=Sim('OrdenDeCompra','Retenida_Por_Falta_Stock');s.fire('at(fechaLimiteStock)');expect('Cancelada_Por_Falta_Stock' in s.path)
scenario('orden: vencimiento de reposición cancela',stock_expired)
scenario('paquete: entrega desde origen rechazada',lambda:rejected(Sim('PaqueteFisico','Recibido_En_Hub_Origen',actorAutorizado=True,evidenciaValida=True),'confirmarEntrega()'))
def attempts_delivery():
 s=Sim('PaqueteFisico','En_Camino_A_Entrega',intentosEntrega=0,actorAutorizado=True)
 for i in range(3):
  s.fire('reportarAusencia()')
  if i<2:expect(s.at('Asignado_A_Ruta_Ultima_Milla'));s.fire('confirmarSalidaRuta()')
 expect(s.at('Retornado_A_Centro_Distribucion') and s.ctx['intentosEntrega']==3)
scenario('paquete: tercera ausencia ordena retorno',attempts_delivery)
def inherited_incident():
 s=Sim('PaqueteFisico','En_Clasificacion',reporteVerificado=True);s.fire('reportarSiniestro()');expect(s.at('Siniestrado_En_Investigacion'))
scenario('paquete: siniestro heredado desde compuesto',inherited_incident)
def vehicle_service():
 s=Sim('VehiculoDeReparto','Estacionado_Fuera_De_Servicio',inspeccionAprobada=True,servicioPendiente=True)
 s.fire('iniciarJornada()');expect(s.at('Requiere_Service'));rejected(s,'asignarRuta()')
scenario('vehículo: servicio vencido bloquea despacho',vehicle_service)
def vehicle_breakdown():
 s=Sim('VehiculoDeReparto','En_Ruta_Operativa');s.fire('fallaMecanicaCritica()');expect(s.at('Varado_En_Averia'))
scenario('vehículo: avería crítica sale de ruta',vehicle_breakdown)
def locker_open():
 s=Sim('CasilleroInteligente','Reservado_Para_Entrega',repartidorAutorizado=True,reservaCoincidente=True,sensorPuertaAbierta=True)
 s.fire('escanearOrden()');expect(s.at('Apertura_Pendiente_Carga'));s.fire('confirmarApertura()');expect(s.at('Puerta_Abierta_Cargando'))
scenario('casillero: comando no equivale a apertura confirmada',locker_open)
def locker_empty():
 s=Sim('CasilleroInteligente','Puerta_Abierta_Cargando',lecturaConfiable=True,puertaCerrada=True,cerraduraTrabada=True,peso=0)
 s.fire('confirmarCierre()');expect(s.at('Reservado_Para_Entrega'))
scenario('casillero: cierre sin peso no confirma depósito',locker_empty)
def locker_unlatched():
 s=Sim('CasilleroInteligente','Puerta_Abierta_Cargando',lecturaConfiable=True,puertaCerrada=True,cerraduraTrabada=False,peso=1)
 s.fire('confirmarCierre()');expect(s.at('Fuera_De_Servicio_Mantenimiento'))
scenario('casillero: cerradura no trabada bloquea servicio',locker_unlatched)
def locker_hardware():
 s=Sim('CasilleroInteligente','Puerta_Abierta_Cargando');s.fire('detectarFalloCerradura()');expect(s.at('Fuera_De_Servicio_Mantenimiento'))
scenario('casillero: fallo de cerradura bloquea servicio',locker_hardware)
def locker_timeout():
 s=Sim('CasilleroInteligente','Ocupado_Esperando_Retiro_Cliente',ahora=72,fechaLimiteRetiro=72)
 s.fire('after(72 h)');expect(s.at('Vencido_Pendiente_Recoleccion'))
scenario('casillero: 72 horas vence retiro',locker_timeout)
scenario('casillero: PIN vencido se rechaza',lambda:rejected(Sim('CasilleroInteligente','Ocupado_Esperando_Retiro_Cliente',codigoValido=True,ahora=73,fechaLimiteRetiro=72),'validarCodigoRetiro()'))
def locker_recover(value,dest):
 s=Sim('CasilleroInteligente','Puerta_Abierta_Cargando',lecturaConfiable=True,recuperacion=value)
 s.fire('reiniciarControlador()');expect(s.at('En_Recuperacion'));s.fire('recibirLecturaSensores()');expect(s.at(dest))
scenario('casillero: reinicio durante carga requiere conciliación',lambda:locker_recover('CARGA_ABIERTA','Puerta_Abierta_Cargando'))
scenario('casillero: ocupación vencida conserva vencimiento',lambda:locker_recover('OCUPADO_VENCIDO','Vencido_Pendiente_Recoleccion'))
scenario('casillero: sensores incoherentes bloquean',lambda:locker_recover('INCOHERENTE','Fuera_De_Servicio_Mantenimiento'))
def return_refund():
 s=Sim('SolicitudDeDevolucion','Aprobada_Para_Reembolso',confirmacionBancariaValida=True)
 s.fire('after(timeoutReembolso)');expect(s.at('Reembolso_En_Conciliacion'));s.fire('confirmarReembolso()');expect('Liquidada_Cerrada' in s.path)
scenario('devolución: conciliación antes de cerrar reembolso',return_refund)
def inventory(last):
 s=Sim('LoteDeInventario','Aprobado_En_Ubicacion_Almacen',existencias=last,cantidad=1)
 s.fire('descontarUnidades()');expect(('Agotado' in s.path) if last==1 else s.at('Activo_En_Picking'))
scenario('inventario: última unidad agota en el mismo evento',lambda:inventory(1))
scenario('inventario: saldo positivo conserva picking',lambda:inventory(2))
scenario('inventario: cantidad excesiva se rechaza',lambda:rejected(Sim('LoteDeInventario','Activo_En_Picking',existencias=1,cantidad=2),'descontarUnidades()'))
scenario('conductor: curso sin Compliance no reactiva',lambda:rejected(Sim('CuentaDeConductor','Suspendido_Por_Bajo_Desempeno',cursoAprobado=True,complianceAutoriza=False,fraudeConfirmado=False),'completarReentrenamiento()'))
def driver_fraud():
 s=Sim('CuentaDeConductor','En_Linea_Disponible',fraudeConfirmado=True,fakeGPS=True,sustraccionPaquetes=False)
 s.fire('detectarFraude()');expect('Expulsado_Permanente' in s.path);rejected(s,'completarReentrenamiento()')
scenario('conductor: fraude confirmado expulsa sin retorno',driver_fraud)
def dispute():
 s=Sim('DisputaBancaria','En_Arbitraje_Bancario',firmaValida=True,fallo='A_FAVOR_EMPRESA')
 s.fire('after(45 dias)');expect(s.at('En_Seguimiento_Plazo_Excedido'));s.fire('recibirFallo()');expect('Ganada_Fondos_Liberados' in s.path)
scenario('disputa: 45 días escala sin inventar victoria',dispute)
def deadline():
 s=Sim('DisputaBancaria','En_Recoleccion_De_Evidencias');s.fire('after(7 dias)');expect('Perdida_Con_Penalizacion' in s.path)
scenario('disputa: siete días sin evidencia produce pérdida',deadline)

def recovered_pending(source,event,**context):
 s=Sim('PaqueteFisico',source,**context);s.fire(event);expect(s.at('Recuperado_Pendiente_Recepcion'))
scenario('recuperación: siniestro recuperable espera recepción',lambda:recovered_pending('Siniestrado_En_Investigacion','cerrarInvestigacion()',supervisorAutorizado=True,recuperable=True))
scenario('recuperación: hallazgo no prueba recepción',lambda:recovered_pending('Extraviado','confirmarHallazgo()',supervisorAutorizado=True,identidadConfirmada=True))
def receive_recovered(hub='ORIGEN',identity=True,receipt=True,accepted=True):
 s=Sim('PaqueteFisico','Recuperado_Pendiente_Recepcion',supervisorAutorizado=True,identidadConfirmada=identity,recepcionFisicaConfirmada=receipt,hubRecepcion=hub)
 if accepted:s.fire('confirmarRecepcionRecuperado()');expect(s.at('Recibido_En_Hub_Origen'if hub=='ORIGEN'else'En_Hub_Destino'))
 else:rejected(s,'confirmarRecepcionRecuperado()')
scenario('recuperación: sin recepción física se rechaza',lambda:receive_recovered(receipt=False,accepted=False))
scenario('recuperación: sin identidad se rechaza',lambda:receive_recovered(identity=False,accepted=False))
scenario('recuperación: hub desconocido se rechaza',lambda:receive_recovered(hub='OTRO',accepted=False))
scenario('recuperación: escaneo de origen no salta el interhub',lambda:receive_recovered('ORIGEN'))
scenario('recuperación: escaneo de destino reanuda allí',lambda:receive_recovered('DESTINO'))
def unsafe_close(state,event):
 s=Sim('CasilleroInteligente',state,lecturaConfiable=True,puertaCerrada=True,cerraduraTrabada=False,peso=1,ahora=10,fechaLimiteRetiro=72)
 s.fire(event);expect(s.at('Fuera_De_Servicio_Mantenimiento'))
for state in ('Puerta_Abierta_Cargando','Puerta_Abierta_Retirando','Puerta_Abierta_Recolectando'):
 scenario('casillero: cierre sin traba en '+state,lambda state=state:unsafe_close(state,'confirmarCierre()'))
 scenario('casillero: timeout de cierre en '+state,lambda state=state:unsafe_close(state,'after(timeoutCierre)'))
def driver_leave(pending):
 s=Sim('CuentaDeConductor','Desconectado',identidadVerificada=True,paquetesPendientes=pending,obligacionesOperativasPendientes=False,fraudeConfirmado=False)
 if pending:rejected(s,'solicitarBaja()')
 else:s.fire('solicitarBaja()');expect('Dado_De_Baja'in s.path)
scenario('conductor: baja con custodia pendiente se rechaza',lambda:driver_leave(True))
scenario('conductor: baja verificada cierra contrato',lambda:driver_leave(False))
def followup(entity,state):
 s=Sim(entity,state);s.fire('at(proximaFechaSeguimiento)');expect(s.at(state))
scenario('pago: seguimiento manual no cambia resultado',lambda:followup('TransaccionDePago','En_Revision_Manual'))
scenario('devolución: seguimiento no repite reembolso',lambda:followup('SolicitudDeDevolucion','Reembolso_En_Conciliacion'))
result={'status':'passed' if not ERRORS else 'failed','checks':len(CHECKS),'passed':sum(c['passed'] for c in CHECKS),'scenario_count':sum(c['check'].startswith('Escenario:') for c in CHECKS),'errors':ERRORS,'entities':summary,'details':CHECKS,'scope':'Análisis estructural, topología sin satisfacibilidad de guardas y simulaciones seleccionadas con efectos locales. No es una certificación de UML completa ni una prueba de apertura/renderizado en StarUML.'}
(BASE/'Verificacion_Rol2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('details','entities')},ensure_ascii=False,indent=2))
if ERRORS:raise SystemExit(1)
