# Acciones e integraciones propuestas

Los nombres son contratos de diseño. No implican que existan conexiones reales con bancos, sensores o microservicios. `entry` se ejecuta al entrar, `do` permanece activa y `exit` limpia al salir. Las transiciones internas evitan la reentrada.

Los comandos externos se despachan después del commit local mediante outbox y una clave idempotente. La confirmación del dispositivo o banco regresa como evento distinto.

| Entidad | Estado | Compartimento | Acción del modelo | Integración prevista |
|---|---|---|---|---|
| OrdenDeCompra | Esperando_Autorizacion_Pago | entry | `conservarFechaLimitePago()` | Servicios propuestos de órdenes, inventario y compensaciones; pasarela bancaria mediante outbox. |
| OrdenDeCompra | Esperando_Autorizacion_Pago | do | `observarAutorizacion()` | Servicios propuestos de órdenes, inventario y compensaciones; pasarela bancaria mediante outbox. |
| OrdenDeCompra | Esperando_Autorizacion_Pago | exit | `cerrarEsperaPago()` | Servicios propuestos de órdenes, inventario y compensaciones; pasarela bancaria mediante outbox. |
| OrdenDeCompra | Retenida_Por_Falta_Stock | entry | `calcularFechaLimiteStockSiNoExiste()` | Servicios propuestos de órdenes, inventario y compensaciones; pasarela bancaria mediante outbox. |
| OrdenDeCompra | Retenida_Por_Falta_Stock | do | `observarReposicion()` | Servicios propuestos de órdenes, inventario y compensaciones; pasarela bancaria mediante outbox. |
| OrdenDeCompra | Retenida_Por_Falta_Stock | exit | `cerrarEsperaStock()` | Servicios propuestos de órdenes, inventario y compensaciones; pasarela bancaria mediante outbox. |
| OrdenDeCompra | Cancelada_Por_Timeout | entry | `liberarReservaYSolicitarCompensacionIdempotente()` | Servicios propuestos de órdenes, inventario y compensaciones; pasarela bancaria mediante outbox. |
| OrdenDeCompra | Cancelada_Por_Usuario | entry | `liberarReservaYSolicitarCompensacionIdempotente()` | Servicios propuestos de órdenes, inventario y compensaciones; pasarela bancaria mediante outbox. |
| OrdenDeCompra | Cancelada_Por_Falta_Stock | entry | `liberarReservaYSolicitarCompensacionIdempotente()` | Servicios propuestos de órdenes, inventario y compensaciones; pasarela bancaria mediante outbox. |
| TransaccionDePago | Iniciada | entry | `inicializarIntentosTotalesEnCero()` | Pasarela y banco emisor, servicio antifraude y conciliación; webhooks firmados. |
| TransaccionDePago | En_Analisis_Antifraude | do | `evaluarRiesgo()` | Pasarela y banco emisor, servicio antifraude y conciliación; webhooks firmados. |
| TransaccionDePago | Esperando_Respuesta_Pasarela | entry | `enviarIntentoConClaveIdempotencia()` | Pasarela y banco emisor, servicio antifraude y conciliación; webhooks firmados. |
| TransaccionDePago | Esperando_Respuesta_Pasarela | do | `observarRespuestaPasarela()` | Pasarela y banco emisor, servicio antifraude y conciliación; webhooks firmados. |
| TransaccionDePago | Esperando_Respuesta_Pasarela | exit | `cerrarObservadorPasarela()` | Pasarela y banco emisor, servicio antifraude y conciliación; webhooks firmados. |
| TransaccionDePago | En_Desafio_3D_Secure | entry | `presentarDesafio3DS()` | Pasarela y banco emisor, servicio antifraude y conciliación; webhooks firmados. |
| TransaccionDePago | En_Desafio_3D_Secure | do | `esperarValidacion3DS()` | Pasarela y banco emisor, servicio antifraude y conciliación; webhooks firmados. |
| TransaccionDePago | En_Conciliacion | entry | `consultarResultadoSinNuevoCargo()` | Pasarela y banco emisor, servicio antifraude y conciliación; webhooks firmados. |
| TransaccionDePago | En_Revision_Manual | entry | `abrirIncidenciaFinanciera()` | Pasarela y banco emisor, servicio antifraude y conciliación; webhooks firmados. |
| PaqueteFisico | Manifiesto_Creado | entry | `inicializarIntentosEntregaEnCero()` | Servicio propuesto de tracking y custodia, GPS del transportista y notificaciones. |
| PaqueteFisico | En_Camino_A_Entrega | entry | `registrarSalidaRuta()` | Servicio propuesto de tracking y custodia, GPS del transportista y notificaciones. |
| PaqueteFisico | En_Camino_A_Entrega | do | `monitorearUbicacionGPS()` | Servicio propuesto de tracking y custodia, GPS del transportista y notificaciones. |
| PaqueteFisico | En_Camino_A_Entrega | exit | `cerrarSeguimientoDeEtapa()` | Servicio propuesto de tracking y custodia, GPS del transportista y notificaciones. |
| PaqueteFisico | Perdida_Confirmada | entry | `solicitarCompensacionIdempotente()` | Servicio propuesto de tracking y custodia, GPS del transportista y notificaciones. |
| VehiculoDeReparto | En_Ruta_Operativa | do | `monitorearTelemetria()` | Telemetría de flota, despacho y gestión de mantenimiento propuestos. |
| VehiculoDeReparto | Varado_En_Averia | entry | `alertarYCoordinarTransbordo()` | Telemetría de flota, despacho y gestión de mantenimiento propuestos. |
| CasilleroInteligente | Apertura_Pendiente_Carga | entry | `enviarComandoAperturaConOperacionId()` | Controlador IoT, sensores y cerradura; servicios propuestos de reserva, OTP y mantenimiento. |
| CasilleroInteligente | Ocupado_Esperando_Retiro_Cliente | entry | `conservarFechaLimiteYNotificarCodigo()` | Controlador IoT, sensores y cerradura; servicios propuestos de reserva, OTP y mantenimiento. |
| CasilleroInteligente | Ocupado_Esperando_Retiro_Cliente | do | `supervisarSensores()` | Controlador IoT, sensores y cerradura; servicios propuestos de reserva, OTP y mantenimiento. |
| CasilleroInteligente | Ocupado_Esperando_Retiro_Cliente | exit | `invalidarCodigoRetiro()` | Controlador IoT, sensores y cerradura; servicios propuestos de reserva, OTP y mantenimiento. |
| CasilleroInteligente | Apertura_Pendiente_Retiro | entry | `enviarComandoAperturaConOperacionId()` | Controlador IoT, sensores y cerradura; servicios propuestos de reserva, OTP y mantenimiento. |
| CasilleroInteligente | Apertura_Pendiente_Recoleccion | entry | `enviarComandoAperturaConOperacionId()` | Controlador IoT, sensores y cerradura; servicios propuestos de reserva, OTP y mantenimiento. |
| CasilleroInteligente | Alarma_Violacion_Seguridad | entry | `bloquearYAlertarSeguridad()` | Controlador IoT, sensores y cerradura; servicios propuestos de reserva, OTP y mantenimiento. |
| CasilleroInteligente | Fuera_De_Servicio_Mantenimiento | entry | `bloquearAsignacionesYAbrirIncidencia()` | Controlador IoT, sensores y cerradura; servicios propuestos de reserva, OTP y mantenimiento. |
| CasilleroInteligente | En_Recuperacion | entry | `bloquearAsignacionesYLeerRegistro()` | Controlador IoT, sensores y cerradura; servicios propuestos de reserva, OTP y mantenimiento. |
| CasilleroInteligente | En_Recuperacion | do | `consultarPuertaCerraduraYPeso()` | Controlador IoT, sensores y cerradura; servicios propuestos de reserva, OTP y mantenimiento. |
| TicketDeSoporte | Registrado_En_Cola | entry | `asignarNumeroTicket()` | Mesa de ayuda y temporizador de SLA propuestos. |
| TicketDeSoporte | En_Espera_Respuesta_Usuario | entry | `conservarFechaLimiteRespuesta()` | Mesa de ayuda y temporizador de SLA propuestos. |
| TicketDeSoporte | En_Espera_Respuesta_Usuario | exit | `cerrarEsperaRespuesta()` | Mesa de ayuda y temporizador de SLA propuestos. |
| TicketDeSoporte | Escalado_Nivel_2_Ingenieria | do | `monitorearSLANivel2()` | Mesa de ayuda y temporizador de SLA propuestos. |
| TicketDeSoporte | Resuelto_Esperando_Confirmacion | entry | `conservarFechaLimiteConfirmacion()` | Mesa de ayuda y temporizador de SLA propuestos. |
| SolicitudDeDevolucion | Aprobada_Generando_Guia_Retorno | entry | `emitirGuiaRetorno()` | Servicio propuesto de logística inversa, almacén y pasarela de reembolsos. |
| SolicitudDeDevolucion | Recibida_En_Inspeccion_Calidad | do | `inspeccionarProducto()` | Servicio propuesto de logística inversa, almacén y pasarela de reembolsos. |
| SolicitudDeDevolucion | Aprobada_Para_Reembolso | entry | `solicitarReembolsoIdempotente()` | Servicio propuesto de logística inversa, almacén y pasarela de reembolsos. |
| SolicitudDeDevolucion | Liquidada_Cerrada | entry | `enviarComprobanteReembolso()` | Servicio propuesto de logística inversa, almacén y pasarela de reembolsos. |
| SolicitudDeDevolucion | Reembolso_En_Conciliacion | entry | `consultarReembolsoConClaveOriginal()` | Servicio propuesto de logística inversa, almacén y pasarela de reembolsos. |
| LoteDeInventario | Recibido_En_Cuarentena | entry | `bloquearDisponibilidad()` | Servicio propuesto de inventario y control de calidad; alertas de recall del proveedor. |
| LoteDeInventario | Bloqueado_Por_Siniestro | entry | `notificarSupervisor()` | Servicio propuesto de inventario y control de calidad; alertas de recall del proveedor. |
| LoteDeInventario | Inmovilizado_Por_Recall | entry | `congelarStock()` | Servicio propuesto de inventario y control de calidad; alertas de recall del proveedor. |
| CuentaDeConductor | Registro_Incompleto | entry | `registrarSeguimiento()` | Servicio propuesto de identidad, Compliance, despacho y desempeño. |
| CuentaDeConductor | Documentacion_En_Validacion | do | `verificarAntecedentes()` | Servicio propuesto de identidad, Compliance, despacho y desempeño. |
| CuentaDeConductor | En_Linea_Disponible | do | `transmitirUbicacionGPS()` | Servicio propuesto de identidad, Compliance, despacho y desempeño. |
| CuentaDeConductor | Suspendido_Por_Bajo_Desempeno | entry | `asignarCursoReentrenamiento()` | Servicio propuesto de identidad, Compliance, despacho y desempeño. |
| CuentaDeConductor | Expulsado_Permanente | entry | `bloquearAccesoPermanente()` | Servicio propuesto de identidad, Compliance, despacho y desempeño. |
| DisputaBancaria | Notificada_Por_Red_Bancaria | entry | `retenerFondosYRegistrarFechaNotificacion()` | Red bancaria y servicio propuesto de evidencias, contabilidad y seguimiento. |
| DisputaBancaria | En_Recoleccion_De_Evidencias | entry | `conservarFechaLimiteEvidencias()` | Red bancaria y servicio propuesto de evidencias, contabilidad y seguimiento. |
| DisputaBancaria | Evidencias_Presentadas_Al_Emisor | entry | `registrarSeguimiento()` | Red bancaria y servicio propuesto de evidencias, contabilidad y seguimiento. |
| DisputaBancaria | En_Arbitraje_Bancario | do | `monitorearPlazoArbitraje()` | Red bancaria y servicio propuesto de evidencias, contabilidad y seguimiento. |
| DisputaBancaria | En_Seguimiento_Plazo_Excedido | entry | `escalarABancoYConservarFondosRetenidos()` | Red bancaria y servicio propuesto de evidencias, contabilidad y seguimiento. |
