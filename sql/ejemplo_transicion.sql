-- Ejecutar después de auditoria_estados.sql en una base vacía.
-- Subconjunto ejecutable de PaqueteFisico: iniciarClasificacion y confirmarEntrega.
-- Las verificaciones de identidad y evidencia las realiza el backend; no son datos
-- que deba decidir el cliente. Las guardas del catálogo son documentación, no código.
INSERT INTO tipo_entidad VALUES ('PAQUETE_FISICO','SMD_PaqueteFisico');
INSERT INTO estado(tipo_entidad,codigo,es_final,es_compuesto) VALUES
 ('PAQUETE_FISICO','Manifiesto_Creado',false,false),
 ('PAQUETE_FISICO','Bajo_Custodia',false,true),
 ('PAQUETE_FISICO','Entregado_Exitosamente',true,false);
INSERT INTO estado(tipo_entidad,codigo,estado_padre_id)
SELECT 'PAQUETE_FISICO',v.codigo,c.id
FROM (VALUES ('Recibido_En_Hub_Origen'),('En_Clasificacion'),('En_Camino_A_Entrega'))v(codigo)
JOIN estado c ON c.tipo_entidad='PAQUETE_FISICO' AND c.codigo='Bajo_Custodia';
INSERT INTO transicion_permitida(tipo_entidad,estado_origen_id,evento,guarda,estado_destino_id)
SELECT 'PAQUETE_FISICO',o.id,v.evento,v.guarda,d.id
FROM (VALUES
 ('Recibido_En_Hub_Origen','iniciarClasificacion()','[actorAutorizado]','En_Clasificacion'),
 ('En_Camino_A_Entrega','confirmarEntrega()','[actorAutorizado && evidenciaValida]','Entregado_Exitosamente')
)v(origen,evento,guarda,destino)
JOIN estado o ON o.tipo_entidad='PAQUETE_FISICO' AND o.codigo=v.origen
JOIN estado d ON d.tipo_entidad='PAQUETE_FISICO' AND d.codigo=v.destino;

CREATE FUNCTION procesar_evento_paquete(
 p_event_id UUID, p_paquete UUID, p_evento TEXT, p_version INT,
 p_actor_autorizado BOOLEAN, p_evidencia_valida BOOLEAN,
 p_responsable_tipo VARCHAR(12), p_responsable_id VARCHAR(80), p_payload JSONB
) RETURNS JSONB LANGUAGE plpgsql AS $$
DECLARE
 v_solicitud JSONB; v_previo evento_procesado%ROWTYPE; v_p paquete_fisico%ROWTYPE;
 v_t transicion_permitida%ROWTYPE; v_motivo TEXT; v_hist BIGINT;
 v_destino INT; v_version INT; v_resultado JSONB;
BEGIN
 IF p_event_id IS NULL OR p_paquete IS NULL OR p_evento IS NULL OR p_version IS NULL
    OR p_actor_autorizado IS NULL OR p_evidencia_valida IS NULL
    OR p_responsable_tipo IS NULL OR p_responsable_id IS NULL OR p_payload IS NULL
 THEN RAISE EXCEPTION 'PETICION_INCOMPLETA'; END IF;
 IF p_responsable_tipo NOT IN ('USUARIO','SISTEMA','DISPOSITIVO','EXTERNO')
 THEN RAISE EXCEPTION 'RESPONSABLE_INVALIDO'; END IF;
 v_solicitud=jsonb_build_object('paquete',p_paquete,'evento',p_evento,'version',p_version,
  'actor',p_actor_autorizado,'evidencia',p_evidencia_valida,
  'responsableTipo',p_responsable_tipo,'responsableId',p_responsable_id,'payload',p_payload);
 -- Serializa el mismo eventId durante esta transacción; no implica atomicidad externa.
 PERFORM pg_advisory_xact_lock(hashtextextended(p_event_id::TEXT,0));
 SELECT * INTO v_previo FROM evento_procesado WHERE event_id=p_event_id;
 IF FOUND THEN
  IF v_previo.solicitud<>v_solicitud THEN RAISE EXCEPTION 'EVENT_ID_REUTILIZADO'; END IF;
  RETURN v_previo.resultado;
 END IF;
 SELECT * INTO v_p FROM paquete_fisico WHERE id=p_paquete;
 IF NOT FOUND THEN RAISE EXCEPTION 'PAQUETE_INEXISTENTE'; END IF;
 INSERT INTO evento_procesado(event_id,solicitud) VALUES(p_event_id,v_solicitud);
 IF NOT p_actor_autorizado THEN v_motivo='NO_AUTORIZADO';
 ELSIF v_p.version<>p_version THEN v_motivo='CONFLICTO_VERSION';
 ELSE
  SELECT * INTO v_t FROM transicion_permitida
   WHERE tipo_entidad='PAQUETE_FISICO' AND estado_origen_id=v_p.estado_actual_id AND evento=p_evento;
  IF NOT FOUND THEN v_motivo='SIN_TRANSICION';
  ELSIF p_evento='confirmarEntrega()' AND NOT p_evidencia_valida THEN v_motivo='GUARDA_FALSA';
  ELSIF p_evento NOT IN ('iniciarClasificacion()','confirmarEntrega()') THEN v_motivo='SIN_TRANSICION';
  END IF;
 END IF;
 IF v_motivo IS NULL THEN
  -- RETURNING es la única fuente del historial aceptado. Cero UPDATE implica cero historial.
  WITH cambiado AS (
   UPDATE paquete_fisico p SET estado_actual_id=v_t.estado_destino_id,version=p.version+1
    WHERE p.id=p_paquete AND p.version=p_version AND p.estado_actual_id=v_p.estado_actual_id
    RETURNING p.*
  )
  INSERT INTO historial_transiciones_estado(tipo_entidad,entidad_id,transicion_id,
   estado_origen_id,estado_destino_id,evento,event_id,responsable_tipo,responsable_id,
   ocurrido_en,version_resultante,payload)
  SELECT 'PAQUETE_FISICO',c.id,v_t.id,v_p.estado_actual_id,c.estado_actual_id,p_evento,
   p_event_id,p_responsable_tipo,p_responsable_id,now(),c.version,p_payload FROM cambiado c
  RETURNING id,estado_destino_id,version_resultante INTO v_hist,v_destino,v_version;
  IF v_hist IS NULL THEN v_motivo='CONFLICTO_VERSION';
  ELSE
   INSERT INTO outbox_efecto_externo(historial_id,destino,operacion,idempotency_key,payload)
   VALUES(v_hist,'NOTIFICACIONES','notificarCambioEstado()',p_event_id,p_payload);
   v_resultado=jsonb_build_object('resultado','ACEPTADO','estadoDestinoId',v_destino,'version',v_version);
  END IF;
 END IF;
 IF v_motivo IS NOT NULL THEN
  INSERT INTO intento_transicion_rechazado(tipo_entidad,entidad_id,estado_actual_id,evento,
   event_id,motivo,responsable_tipo,responsable_id,payload)
  VALUES('PAQUETE_FISICO',p_paquete,v_p.estado_actual_id,p_evento,p_event_id,v_motivo,
   p_responsable_tipo,p_responsable_id,p_payload);
  v_resultado=jsonb_build_object('resultado','RECHAZADO','motivo',v_motivo);
 END IF;
 UPDATE evento_procesado SET resultado=v_resultado WHERE event_id=p_event_id;
 RETURN v_resultado;
END $$;

INSERT INTO paquete_fisico(id,codigo_rastreo,estado_actual_id,version)
SELECT '11111111-1111-1111-1111-111111111111','PF-0001',id,1 FROM estado
 WHERE tipo_entidad='PAQUETE_FISICO' AND codigo='Recibido_En_Hub_Origen';
-- Aceptada. Segundo envío idéntico devuelve el mismo resultado sin cambiar otra vez.
SELECT procesar_evento_paquete('aaaaaaaa-0000-0000-0000-000000000001',
 '11111111-1111-1111-1111-111111111111','iniciarClasificacion()',1,true,true,
 'USUARIO','operador-hub-17','{"hub":"ORIGEN"}');
-- Rechazada: el paquete está en clasificación y no puede marcarse como entregado.
SELECT procesar_evento_paquete('aaaaaaaa-0000-0000-0000-000000000002',
 '11111111-1111-1111-1111-111111111111','confirmarEntrega()',2,true,true,
 'USUARIO','operador-hub-17','{}');
