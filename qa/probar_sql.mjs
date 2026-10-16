import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const {PGlite}=await import(process.env.PGLITE_MODULE || '@electric-sql/pglite');
const base=path.dirname(fileURLToPath(import.meta.url));
const db=new PGlite();
const checks=[];
function check(name,ok){checks.push({name,passed:!!ok});if(!ok)throw Error(name);}
async function scalar(sql){return Object.values((await db.query(sql)).rows[0])[0];}
async function fails(sql){try{await db.exec(sql);return false;}catch{return true;}}
async function call(id,pkg,event,version,actor=true,evidence=true,payload={}){
 return (await db.query(`SELECT procesar_evento_paquete($1::uuid,$2::uuid,$3,$4,$5,$6,'USUARIO','operador-hub-17',$7::jsonb) AS r`,[id,pkg,event,version,actor,evidence,JSON.stringify(payload)])).rows[0].r;
}
const pkg='11111111-1111-1111-1111-111111111111';
const id=n=>'bbbbbbbb-0000-0000-0000-'+String(n).padStart(12,'0');
await db.exec(await fs.readFile(path.join(base,'../sql/auditoria_estados.sql'),'utf8'));
await db.exec(await fs.readFile(path.join(base,'../sql/ejemplo_transicion.sql'),'utf8'));
const version=await scalar('SELECT version()');
check('PostgreSQL ejecuta DDL y función',version.startsWith('PostgreSQL'));
check('Cambio aceptado actualiza estado y versión',await scalar(`SELECT p.version=2 AND e.codigo='En_Clasificacion' FROM paquete_fisico p JOIN estado e ON e.id=p.estado_actual_id WHERE p.id='${pkg}'`));
check('Un historial aceptado',Number(await scalar('SELECT count(*) FROM historial_transiciones_estado'))===1);
check('Entrega prematura rechazada',await scalar(`SELECT count(*)=1 AND min(motivo)='SIN_TRANSICION' FROM intento_transicion_rechazado`));
check('Un efecto en outbox',Number(await scalar('SELECT count(*) FROM outbox_efecto_externo'))===1);
const replay=await call('aaaaaaaa-0000-0000-0000-000000000001',pkg,'iniciarClasificacion()',1,true,true,{hub:'ORIGEN'});
check('Repetición aceptada devuelve resultado previo',replay.resultado==='ACEPTADO'&&replay.version===2&&Number(await scalar('SELECT count(*) FROM historial_transiciones_estado'))===1);
const rejection=await call('aaaaaaaa-0000-0000-0000-000000000002',pkg,'confirmarEntrega()',2);
check('Repetición rechazada no duplica intentos',rejection.motivo==='SIN_TRANSICION'&&Number(await scalar('SELECT count(*) FROM intento_transicion_rechazado'))===1);
let reused=false;try{await call('aaaaaaaa-0000-0000-0000-000000000001',pkg,'iniciarClasificacion()',1,true,true,{hub:'DESTINO'});}catch(e){reused=String(e).includes('EVENT_ID_REUTILIZADO');}
check('Mismo ID con otro contenido se rechaza',reused);
check('Actor no autorizado no cambia estado',(await call(id(3),pkg,'iniciarClasificacion()',2,false)).motivo==='NO_AUTORIZADO');
check('Versión antigua se rechaza',(await call(id(4),pkg,'iniciarClasificacion()',1)).motivo==='CONFLICTO_VERSION');
const p2='22222222-2222-2222-2222-222222222222';
await db.exec(`INSERT INTO paquete_fisico(id,codigo_rastreo,estado_actual_id) SELECT '${p2}','PF-0002',id FROM estado WHERE codigo='En_Camino_A_Entrega'`);
check('Entrega sin evidencia se rechaza',(await call(id(5),p2,'confirmarEntrega()',0,true,false)).motivo==='GUARDA_FALSA');
check('Entrega válida desde ruta se acepta',(await call(id(6),p2,'confirmarEntrega()',0)).resultado==='ACEPTADO');
await db.exec(`INSERT INTO tipo_entidad VALUES ('CASILLERO','SMD_CasilleroInteligente');INSERT INTO estado(tipo_entidad,codigo) VALUES('CASILLERO','Vacio_Disponible');`);
check('FK impide estado de otra entidad',await fails(`UPDATE paquete_fisico SET estado_actual_id=(SELECT id FROM estado WHERE codigo='Vacio_Disponible') WHERE id='${pkg}'`));
check('Historial no permite UPDATE',await fails('UPDATE historial_transiciones_estado SET evento=evento'));
check('Historial no permite DELETE',await fails('DELETE FROM historial_transiciones_estado'));
const p3='33333333-3333-3333-3333-333333333333';
await db.exec(`INSERT INTO paquete_fisico(id,codigo_rastreo,estado_actual_id) SELECT '${p3}','PF-0003',id FROM estado WHERE codigo='Recibido_En_Hub_Origen'`);
await db.exec('BEGIN');await call(id(7),p3,'iniciarClasificacion()',0);await db.exec('ROLLBACK');
check('Rollback revierte dominio, evento, historial y outbox',await scalar(`SELECT (SELECT version FROM paquete_fisico WHERE id='${p3}')=0 AND NOT EXISTS(SELECT 1 FROM evento_procesado WHERE event_id='${id(7)}') AND NOT EXISTS(SELECT 1 FROM historial_transiciones_estado WHERE event_id='${id(7)}') AND NOT EXISTS(SELECT 1 FROM outbox_efecto_externo WHERE idempotency_key='${id(7)}')`));
const result={status:'passed',checks:checks.length,passed:checks.filter(c=>c.passed).length,postgres:version,pglite:'0.5.10',scope:'Ejemplo local con dos eventos. Sin bancos, sensores ni prueba de concurrencia distribuida.',details:checks};
await fs.writeFile(path.join(base,'Verificacion_SQL.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({...result,details:undefined},null,2));await db.close();
