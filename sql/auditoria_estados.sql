-- =====================================================================
-- LogiFlow 360° — Persistencia y auditoría de estados (PostgreSQL 13+)
-- PROPUESTA del Rol 4. Los códigos de estado deben coincidir con el .mdj.
-- =====================================================================

-- 1) Catálogo de las 10 entidades con ciclo de vida
CREATE TABLE tipo_entidad (
    codigo      VARCHAR(40) PRIMARY KEY,          -- 'PAQUETE_FISICO', 'TRANSACCION_PAGO', ...
    diagrama    VARCHAR(60) NOT NULL UNIQUE       -- 'SMD_PaqueteFisico'
);

-- 2) Estados válidos por entidad (uno por cada estado del diagrama)
CREATE TABLE estado (
    id            SERIAL PRIMARY KEY,
    tipo_entidad  VARCHAR(40) NOT NULL REFERENCES tipo_entidad(codigo),
    codigo        VARCHAR(60) NOT NULL,           -- 'Recibido_En_Hub_Origen' (igual que en el .mdj)
    es_final      BOOLEAN     NOT NULL DEFAULT FALSE,  -- precede a un Final State
    es_compuesto  BOOLEAN     NOT NULL DEFAULT FALSE,  -- 'Bajo_Custodia', 'En_Operacion', ...
    estado_padre_id INT,                          -- subestado -> su estado compuesto
    UNIQUE (tipo_entidad, codigo),
    UNIQUE (id, tipo_entidad),                    -- permite FKs compuestas (estado ∈ entidad)
    FOREIGN KEY (estado_padre_id, tipo_entidad) REFERENCES estado(id, tipo_entidad)
);
-- Regla: el estado actual de una entidad siempre es un estado simple (hoja);
-- el compuesto se deduce por estado_padre_id. Las transiciones dibujadas desde el
-- borde del compuesto se cargan en transicion_permitida una vez por cada subestado.

-- 3) Transiciones permitidas = filas de la matriz Estado-Evento.
--    origen NULL representa la transición que sale del Initial pseudoestado.
CREATE TABLE transicion_permitida (
    id                 SERIAL PRIMARY KEY,
    tipo_entidad       VARCHAR(40) NOT NULL REFERENCES tipo_entidad(codigo),
    estado_origen_id   INT,
    evento             VARCHAR(60) NOT NULL,      -- 'confirmarEntrega()'; vacío = transición de finalización
    guarda             VARCHAR(200),              -- texto documental: '[actorAutorizado && evidenciaValida]'
    estado_destino_id  INT NOT NULL,
    FOREIGN KEY (estado_origen_id,  tipo_entidad) REFERENCES estado(id, tipo_entidad),
    FOREIGN KEY (estado_destino_id, tipo_entidad) REFERENCES estado(id, tipo_entidad),
    UNIQUE (id, tipo_entidad)
);
-- Unicidad tratando NULL (Initial) como un valor más
CREATE UNIQUE INDEX ux_transicion ON transicion_permitida
    (tipo_entidad, COALESCE(estado_origen_id, 0), evento, estado_destino_id);

-- 4) Ejemplo de entidad concreta: cada tabla de dominio guarda su estado actual
CREATE TABLE paquete_fisico (
    id                 UUID PRIMARY KEY,
    codigo_rastreo     VARCHAR(40) NOT NULL UNIQUE,
    tipo_entidad       VARCHAR(40) NOT NULL DEFAULT 'PAQUETE_FISICO'
                       CHECK (tipo_entidad = 'PAQUETE_FISICO'),
    estado_actual_id   INT NOT NULL,
    intentos_entrega   SMALLINT NOT NULL DEFAULT 0 CHECK (intentos_entrega BETWEEN 0 AND 3),
    version            INT NOT NULL DEFAULT 0,    -- bloqueo optimista
    FOREIGN KEY (estado_actual_id, tipo_entidad) REFERENCES estado(id, tipo_entidad)
);

-- Resultado global por eventId: cubre aceptados y rechazados y compara la petición.
-- La función de ejemplo completa resultado dentro de la misma transacción local.
CREATE TABLE evento_procesado (
    event_id UUID PRIMARY KEY,
    solicitud JSONB NOT NULL,
    resultado JSONB,
    registrado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5) Historial: SOLO cambios ACEPTADOS (append-only)
CREATE TABLE historial_transiciones_estado (
    id                  BIGSERIAL PRIMARY KEY,
    tipo_entidad        VARCHAR(40) NOT NULL REFERENCES tipo_entidad(codigo),
    entidad_id          UUID        NOT NULL,     -- id de la fila en la tabla de dominio
    transicion_id       INT         NOT NULL,     -- fila de la matriz que se aplicó
    estado_origen_id    INT,                      -- NULL solo al nacer (desde Initial)
    estado_destino_id   INT         NOT NULL,
    evento              VARCHAR(60) NOT NULL,
    event_id            UUID        NOT NULL UNIQUE REFERENCES evento_procesado(event_id),
    responsable_tipo    VARCHAR(12) NOT NULL CHECK (responsable_tipo IN ('USUARIO','SISTEMA','DISPOSITIVO','EXTERNO')),
    responsable_id      VARCHAR(80) NOT NULL,     -- id de usuario, servicio, casillero o pasarela
    ocurrido_en         TIMESTAMPTZ NOT NULL,     -- cuándo pasó en el mundo real
    registrado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),  -- cuándo lo persistimos
    version_resultante  INT         NOT NULL,
    payload             JSONB       NOT NULL DEFAULT '{}'::jsonb,
    FOREIGN KEY (estado_origen_id,  tipo_entidad) REFERENCES estado(id, tipo_entidad),
    FOREIGN KEY (estado_destino_id, tipo_entidad) REFERENCES estado(id, tipo_entidad),
    FOREIGN KEY (transicion_id,     tipo_entidad) REFERENCES transicion_permitida(id, tipo_entidad),
    UNIQUE (tipo_entidad, entidad_id, version_resultante)  -- dos escritores no pueden producir la misma versión
);
CREATE INDEX ix_hist_entidad ON historial_transiciones_estado (tipo_entidad, entidad_id, registrado_en);

-- 6) Intentos RECHAZADOS (fraude, eventos fuera de orden, guardas falsas)
CREATE TABLE intento_transicion_rechazado (
    id                  BIGSERIAL PRIMARY KEY,
    tipo_entidad        VARCHAR(40) NOT NULL REFERENCES tipo_entidad(codigo),
    entidad_id          UUID        NOT NULL,
    estado_actual_id    INT         NOT NULL,     -- estado en que estaba (no cambia)
    evento              VARCHAR(60) NOT NULL,
    event_id            UUID        NOT NULL UNIQUE REFERENCES evento_procesado(event_id),
    motivo              VARCHAR(30) NOT NULL CHECK (motivo IN
                        ('SIN_TRANSICION','GUARDA_FALSA','CONFLICTO_VERSION','NO_AUTORIZADO')),
    responsable_tipo    VARCHAR(12) NOT NULL,
    responsable_id      VARCHAR(80) NOT NULL,
    recibido_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload             JSONB       NOT NULL DEFAULT '{}'::jsonb,
    FOREIGN KEY (estado_actual_id, tipo_entidad) REFERENCES estado(id, tipo_entidad)
);

-- 7) Outbox: efectos externos (banco, casillero, notificaciones) pendientes de ejecutar.
--    Se inserta en la MISMA transacción local que el cambio de estado; un worker lo
--    entrega después con reintentos y una clave de idempotencia hacia el sistema externo.
CREATE TABLE outbox_efecto_externo (
    id                BIGSERIAL PRIMARY KEY,
    historial_id      BIGINT NOT NULL REFERENCES historial_transiciones_estado(id),
    destino           VARCHAR(40) NOT NULL,       -- 'PASARELA_PAGO', 'CASILLERO_IOT', 'NOTIFICACIONES'
    operacion         VARCHAR(60) NOT NULL,
    idempotency_key   UUID NOT NULL UNIQUE,
    estado_envio      VARCHAR(12) NOT NULL DEFAULT 'PENDIENTE'
                      CHECK (estado_envio IN ('PENDIENTE','ENVIADO','CONFIRMADO','FALLIDO')),
    intentos          SMALLINT NOT NULL DEFAULT 0,
    payload           JSONB NOT NULL,
    creado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- El historial no se edita ni se borra (auditoría contable y legal)
CREATE FUNCTION fn_historial_inmutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'historial_transiciones_estado es append-only';
END $$ LANGUAGE plpgsql;

CREATE TRIGGER tr_historial_inmutable
    BEFORE UPDATE OR DELETE ON historial_transiciones_estado
    FOR EACH ROW EXECUTE FUNCTION fn_historial_inmutable();
