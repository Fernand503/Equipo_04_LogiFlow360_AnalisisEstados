# Matrices de transición LogiFlow 360

Fuente semántica: `LogiFlow360_StateModels.mdj`. Hay 219 transiciones; cada identificador NN-TNN corresponde al orden del informe. `Compuesto::Subestado` indica anidación. La documentación procede del campo Documentation del modelo.

La verificación es estructural y usa escenarios seleccionados; no demuestra todas las combinaciones de guardas ni integraciones reales.

## 01 OrdenDeCompra

| ID | Estado origen | Evento | Guarda | Efecto | Estado destino | Tipo | Justificación |
|---|---|---|---|---|---|---|---|
| 01-T01 | Initial | — | — | — | Borrador_En_Carrito | external | La orden nace en el carrito. |
| 01-T02 | Borrador_En_Carrito | presionarCheckout() | [carritoValido && reservaConfirmada] | / registrarFechaLimitePago() | Esperando_Autorizacion_Pago | external | Checkout solo con carrito válido y reserva confirmada |
| 01-T03 | Esperando_Autorizacion_Pago | confirmarPago() | [autorizacionValida && reservaVigente && ahora < fechaLimitePago] | / registrarAutorizacion() | En_Procesamiento_Almacen | external | Pago autorizado dentro del plazo habilita el almacén |
| 01-T04 | Esperando_Autorizacion_Pago | after(30 min) | [!pagoAutorizado] | / registrarCancelacionPorTimeout() | Cancelada_Por_Timeout | external | Sin pago en 30 min se cancela y se libera inventario). |
| 01-T05 | Esperando_Autorizacion_Pago | at(fechaLimitePago) | [!pagoAutorizado] | / registrarCancelacionPorTimeout() | Cancelada_Por_Timeout | external | Vencimiento absoluto persistido: conserva la fecha tras reinicio. Las dos notificaciones de vencimiento se deduplican. |
| 01-T06 | En_Procesamiento_Almacen | confirmarEmpaque() | [stockDisponible && !cancelacionConfirmada] | / registrarEmpaque() | Empacada | external | Empaque solo con stock disponible y sin cancelación confirmada. |
| 01-T07 | En_Procesamiento_Almacen | detectarQuiebreStock() | [!stockDisponible] | / registrarRetencion() | Retenida_Por_Falta_Stock | external | Quiebre de inventario retiene la orden. |
| 01-T08 | Retenida_Por_Falta_Stock | confirmarReposicion() | [stockDisponible && ahora < fechaLimiteStock] | / reservarStockRepuesto() | En_Procesamiento_Almacen | external | Reposición dentro del plazo devuelve la orden a almacén. |
| 01-T09 | Retenida_Por_Falta_Stock | at(fechaLimiteStock) | — | / registrarCancelacionPorStock() | Cancelada_Por_Falta_Stock | external | fechaLimiteStock = sumarDiasHabiles(inicioRetencion,5,calendarioNegocio) |
| 01-T10 | Borrador_En_Carrito | cancelarOrden() | [actorAutorizado] | / registrarCancelacionUsuario() | Cancelada_Por_Usuario | external | Cancelación del usuario antes del empaquetado. |
| 01-T11 | Esperando_Autorizacion_Pago | cancelarOrden() | [actorAutorizado] | / registrarCancelacionUsuario() | Cancelada_Por_Usuario | external | Cancelación del usuario antes del empaquetado |
| 01-T12 | En_Procesamiento_Almacen | cancelarOrden() | [actorAutorizado] | / registrarCancelacionUsuario() | Cancelada_Por_Usuario | external | Cancelación del usuario antes del empaquetado |
| 01-T13 | Retenida_Por_Falta_Stock | cancelarOrden() | [actorAutorizado] | / registrarCancelacionUsuario() | Cancelada_Por_Usuario | external | Cancelación durante la retención por stock. |
| 01-T14 | Empacada | confirmarDespacho() | [manifiestoValido] | / registrarDespacho() | Despachada_En_Ruta | external | Despacho con manifiesto válido |
| 01-T15 | Despachada_En_Ruta | confirmarEntrega() | [evidenciaValida] | / registrarRecepcionCliente() | Completada_Entregada | external | Entrega confirmada solo con evidencia válida. |
| 01-T16 | Cancelada_Por_Timeout | — | — | — | Final | external | Cierre comercial |
| 01-T17 | Cancelada_Por_Usuario | — | — | — | Final | external | Cierre comercial |
| 01-T18 | Cancelada_Por_Falta_Stock | — | — | — | Final | external | Cierre tras agotar la espera de reposición. |
| 01-T19 | Completada_Entregada | — | — | — | Final | external | Fin natural del ciclo comercial. |

## 02 TransaccionDePago

| ID | Estado origen | Evento | Guarda | Efecto | Estado destino | Tipo | Justificación |
|---|---|---|---|---|---|---|---|
| 02-T01 | Initial | — | — | — | Iniciada | external | El registro financiero nace en Iniciada. |
| 02-T02 | Iniciada | iniciarPago() | — | / registrarSolicitud() | En_Analisis_Antifraude | external | Toda transacción pasa por antifraude antes de tocar la pasarela. |
| 02-T03 | En_Analisis_Antifraude | recibirScoring() | [scoringValido] | / guardarScoring() | Choice C1 | external | Solo un scoring válido se evalúa |
| 02-T04 | Choice C1 | — | [riesgo < umbralRiesgo] | / incrementarIntentosTotales() | Esperando_Respuesta_Pasarela | external | Riesgo bajo → pasarela |
| 02-T05 | Choice C1 | — | [riesgo >= umbralRiesgo] | / registrarRechazoRiesgo() | Rechazada_Por_Riesgo | external | Riesgo alto → rechazo inmediato |
| 02-T06 | Esperando_Respuesta_Pasarela | recibirRespuesta() | [firmaValida && correlacionValida] | / guardarResultado() | Choice C2 | external | Solo respuestas firmadas y correlacionadas con la solicitud se aceptan. |
| 02-T07 | Choice C2 | — | [resultado == 'APPROVED'] | / registrarAutorizacion() | Autorizada | external | Autorización bancaria |
| 02-T08 | Choice C2 | — | [resultado == 'REQUIRES_3DS'] | / registrarDesafio() | En_Desafio_3D_Secure | external | El emisor exige autenticación reforzada. |
| 02-T09 | Choice C2 | — | [resultado == 'INSUFFICIENT_FUNDS'] | / registrarRechazoConfirmado() | Rechazada_Por_Fondos | external | Tarjeta declinada por fondos. |
| 02-T10 | Choice C2 | — | [resultado == 'ISSUER_ERROR'] | / registrarErrorConfirmado() | Error_Emisor | external | Error del banco emisor. |
| 02-T11 | Choice C2 | — | [else] | / registrarResultadoIncierto() | En_Conciliacion | external | Resultado desconocido → conciliar |
| 02-T12 | Esperando_Respuesta_Pasarela | after(timeoutPasarela) | — | / registrarIncertidumbre() | En_Conciliacion | external | Parámetro operativo configurable |
| 02-T13 | En_Desafio_3D_Secure | recibirResultado3DS() | [firmaValida && resultado3DS == 'APPROVED'] | / registrarAutorizacion() | Autorizada | external | Desafío 3DS superado. |
| 02-T14 | En_Desafio_3D_Secure | recibirResultado3DS() | [firmaValida && resultado3DS == 'DECLINED'] | / registrarRechazoConfirmado() | Error_Emisor | external | Desafío 3DS fallido |
| 02-T15 | En_Desafio_3D_Secure | after(timeout3DS) | — | / consultarExpiracion3DS() | En_Conciliacion | external | El usuario no completa el SMS |
| 02-T16 | Rechazada_Por_Fondos | reintentarPago() | [intentosTotales < 3 && resultadoPrevioConfirmado] | / incrementarIntentosTotales() | Esperando_Respuesta_Pasarela | external | Reintento manual |
| 02-T17 | Rechazada_Por_Fondos | — | [intentosTotales >= 3] | / registrarLimiteAgotado() | Fallida_Definitiva | external | Límite agotado → falla definitiva sin exigir un cuarto clic. |
| 02-T18 | Rechazada_Por_Fondos | after(timeoutReintento) | [intentosTotales < 3] | / cerrarPorAbandono() | Fallida_Definitiva | external | El cliente no reintenta → cierre por abandono |
| 02-T19 | Error_Emisor | reintentarPago() | [intentosTotales < 3 && resultadoPrevioConfirmado] | / incrementarIntentosTotales() | Esperando_Respuesta_Pasarela | external | Reintento manual tras error del emisor |
| 02-T20 | Error_Emisor | — | [intentosTotales >= 3] | / registrarLimiteAgotado() | Fallida_Definitiva | external | Límite agotado → falla definitiva. |
| 02-T21 | Error_Emisor | after(timeoutReintento) | [intentosTotales < 3] | / cerrarPorAbandono() | Fallida_Definitiva | external | Sin reintento → cierre por abandono. |
| 02-T22 | En_Conciliacion | confirmarResultadoConciliado() | [firmaValida && correlacionValida] | / guardarResultado() | Choice C2 | external | La conciliación reinyecta el resultado verificado en la misma decisión. |
| 02-T23 | En_Conciliacion | after(timeoutConciliacion) | — | / escalarSinNuevoCargo() | En_Revision_Manual | external | Conciliación sin respuesta → revisión humana, sin nuevo cargo. |
| 02-T24 | En_Revision_Manual | resolverRevision() | [resultadoBancarioVerificado] | / guardarResultado() | Choice C2 | external | El resultado verificado por un analista vuelve a la decisión. |
| 02-T25 | Autorizada | consolidarLoteNocturno() | — | / solicitarLiquidacion() | En_Liquidacion | external | El lote bancario nocturno inicia la liquidación |
| 02-T26 | Autorizada | confirmarAnulacion() | [confirmacionBancariaValida] | / registrarAnulacion() | Anulada_Confirmada | external | Anulación solo con confirmación bancaria. |
| 02-T27 | En_Liquidacion | confirmarDeposito() | [confirmacionBancariaValida] | / registrarDeposito() | Liquidada_Depositada | external | Depósito confirmado por el banco. |
| 02-T28 | En_Liquidacion | after(timeoutLiquidacion) | — | / consultarLiquidacion() | En_Conciliacion_Liquidacion | external | Liquidación sin confirmación → conciliación. |
| 02-T29 | En_Conciliacion_Liquidacion | confirmarDeposito() | [confirmacionBancariaValida] | / registrarDeposito() | Liquidada_Depositada | external | La conciliación confirma el depósito. |
| 02-T30 | En_Conciliacion_Liquidacion | confirmarAnulacion() | [confirmacionBancariaValida] | / registrarAnulacion() | Anulada_Confirmada | external | La conciliación confirma la anulación. |
| 02-T31 | En_Revision_Manual | at(proximaFechaSeguimiento) | — | / alertarResponsableYReprogramarSeguimiento() | En_Revision_Manual | internal | Alerta y rearma la fecha sin alterar el resultado ni repetir efectos financieros. |
| 02-T32 | Liquidada_Depositada | — | — | — | Final | external | Fin natural: fondos depositados. |
| 02-T33 | Rechazada_Por_Riesgo | — | — | — | Final | external | Fin: rechazo por riesgo. |
| 02-T34 | Fallida_Definitiva | — | — | — | Final | external | Fin: intentos agotados o abandono. |
| 02-T35 | Anulada_Confirmada | — | — | — | Final | external | Fin: anulación confirmada. |

## 03 PaqueteFisico

| ID | Estado origen | Evento | Guarda | Efecto | Estado destino | Tipo | Justificación |
|---|---|---|---|---|---|---|---|
| 03-T01 | Initial | — | — | — | Manifiesto_Creado | external | El paquete nace como manifiesto. |
| 03-T02 | Bajo_Custodia::Recibido_En_Hub_Origen | iniciarClasificacion() | [actorAutorizado] | / registrarClasificacion() | Bajo_Custodia::En_Clasificacion | external | Clasificación en el hub de origen por actor autorizado. |
| 03-T03 | Bajo_Custodia::En_Clasificacion | confirmarSalidaHub() | [actorAutorizado] | / registrarTransferencia() | Bajo_Custodia::En_Transito_Inter_Hub | external | Salida en camión nodriza con transferencia de custodia. |
| 03-T04 | Bajo_Custodia::En_Transito_Inter_Hub | escanearLlegadaDestino() | [actorAutorizado] | / registrarCustodiaDestino() | Bajo_Custodia::En_Hub_Destino | external | Escaneo de llegada transfiere la custodia al hub destino. |
| 03-T05 | Bajo_Custodia::En_Hub_Destino | asignarRuta() | [actorAutorizado] | / registrarRuta() | Bajo_Custodia::Asignado_A_Ruta_Ultima_Milla | external | Asignación a ruta de última milla. |
| 03-T06 | Bajo_Custodia::Asignado_A_Ruta_Ultima_Milla | confirmarSalidaRuta() | [actorAutorizado] | / registrarSalida() | Bajo_Custodia::En_Camino_A_Entrega | external | Sale a reparto |
| 03-T07 | Bajo_Custodia::En_Camino_A_Entrega | reportarAusencia() | [intentosEntrega < 3] | / incrementarIntentosEntrega() | Bajo_Custodia::Entrega_Fallida_Ausente | external | Destinatario ausente: el contador se incrementa antes de decidir. |
| 03-T08 | Bajo_Custodia::Entrega_Fallida_Ausente | — | [intentosEntrega < 3] | / programarNuevaVisita() | Bajo_Custodia::Asignado_A_Ruta_Ultima_Milla | external | Intentos 1 y 2 → nueva visita. |
| 03-T09 | Manifiesto_Creado | escanearRecepcion() | [etiquetaValida] | / registrarCustodiaOrigen() | Bajo_Custodia::Recibido_En_Hub_Origen | external | Primer escaneo con etiqueta válida inicia la custodia. |
| 03-T10 | Bajo_Custodia::En_Camino_A_Entrega | confirmarEntrega() | [actorAutorizado && evidenciaValida] | / guardarPruebaEntrega() | Entregado_Exitosamente | external | Único camino a entregado: desde En_Camino, con actor autorizado y evidencia. |
| 03-T11 | Bajo_Custodia::Entrega_Fallida_Ausente | — | [intentosEntrega >= 3] | / ordenarRetorno() | Retornado_A_Centro_Distribucion | external | Tercer intento fallido → retorno |
| 03-T12 | Bajo_Custodia | reportarSiniestro() | [reporteVerificado] | / abrirInvestigacion() | Siniestrado_En_Investigacion | external | Daño verificado desde cualquier etapa de custodia. |
| 03-T13 | Bajo_Custodia | reportarExtravio() | [reporteVerificado] | / iniciarBusqueda() | Extraviado | external | Extravío verificado desde cualquier etapa de custodia. |
| 03-T14 | Siniestrado_En_Investigacion | cerrarInvestigacion() | [supervisorAutorizado && recuperable] | / registrarRecuperacion() | Recuperado_Pendiente_Recepcion | external | El hallazgo identifica el paquete; falta confirmar su recepción física. |
| 03-T15 | Siniestrado_En_Investigacion | cerrarInvestigacion() | [supervisorAutorizado && !recuperable] | / registrarPerdidaYObligacionCompensacion() | Perdida_Confirmada | external | No recuperable → pérdida con compensación. |
| 03-T16 | Extraviado | confirmarHallazgo() | [supervisorAutorizado && identidadConfirmada] | / registrarHallazgo() | Recuperado_Pendiente_Recepcion | external | El hallazgo identifica el paquete; falta confirmar su recepción física. |
| 03-T17 | Extraviado | confirmarPerdida() | [supervisorAutorizado && investigacionConcluida] | / registrarPerdidaYObligacionCompensacion() | Perdida_Confirmada | external | Investigación concluida sin hallazgo → pérdida. |
| 03-T18 | Recuperado_Pendiente_Recepcion | confirmarRecepcionRecuperado() | [supervisorAutorizado && identidadConfirmada && recepcionFisicaConfirmada && (hubRecepcion == 'ORIGEN' \|\| hubRecepcion == 'DESTINO')] | / registrarRecepcionFisica() | Choice C1 | external | Solo un escaneo físico verificado permite clasificar el hub de reingreso. |
| 03-T19 | Choice C1 | — | [hubRecepcion == 'ORIGEN'] | / registrarCustodiaOrigen() | Bajo_Custodia::Recibido_En_Hub_Origen | external | Reanuda custodia en el hub físico confirmado por el escaneo. |
| 03-T20 | Choice C1 | — | [hubRecepcion == 'DESTINO'] | / registrarCustodiaDestino() | Bajo_Custodia::En_Hub_Destino | external | Reanuda custodia en el hub físico confirmado por el escaneo. |
| 03-T21 | Entregado_Exitosamente | — | — | — | Final | external | Fin legítimo: entrega cumplida. |
| 03-T22 | Perdida_Confirmada | — | — | — | Final | external | Fin: pérdida confirmada |
| 03-T23 | Retornado_A_Centro_Distribucion | confirmarRetorno() | [recepcionHubConfirmada] | / cerrarCicloDeReparto() | Final | external | La recepción del retorno en el hub cierra el ciclo de reparto. |

## 04 VehiculoDeReparto

| ID | Estado origen | Evento | Guarda | Efecto | Estado destino | Tipo | Justificación |
|---|---|---|---|---|---|---|---|
| 04-T01 | Initial | — | — | — | Estacionado_Fuera_De_Servicio | external | La unidad pasa la noche estacionada. |
| 04-T02 | Estacionado_Fuera_De_Servicio | iniciarJornada() | — | / guardarInspeccionYKilometraje() | Choice C1 | external | Inspección matutina y kilometraje se evalúan en una sola decisión. |
| 04-T03 | Choice C1 | — | [inspeccionAprobada && !servicioPendiente] | / habilitarDisponibilidad() | Disponible_En_Base | external | Inspección aprobada y sin service pendiente. |
| 04-T04 | Choice C1 | — | [servicioPendiente] | / bloquearDespacho() | Requiere_Service | external | Falta de mantenimiento preventivo bloquea la disponibilidad. |
| 04-T05 | Choice C1 | — | [!inspeccionAprobada && !servicioPendiente] | / registrarInspeccionRechazada() | En_Taller_Mantenimiento | external | Inspección rechazada → taller. |
| 04-T06 | Disponible_En_Base | asignarRuta() | [conductorHabilitado && !servicioPendiente] | / registrarAsignacion() | En_Carga_Mercancia | external | Asignación solo con conductor habilitado y sin service pendiente. |
| 04-T07 | En_Carga_Mercancia | confirmarSalida() | [cargaSegura && !servicioPendiente] | / registrarSalida() | En_Ruta_Operativa | external | Salida a la calle con carga asegurada. |
| 04-T08 | En_Ruta_Operativa | finalizarEntregas() | — | / registrarRegreso() | Fin_De_Jornada | external | Regreso al terminar las entregas. |
| 04-T09 | Fin_De_Jornada | cerrarJornada() | [!servicioPendiente] | / registrarEstacionamiento() | Estacionado_Fuera_De_Servicio | external | Cierre normal de jornada. |
| 04-T10 | Fin_De_Jornada | cerrarJornada() | [servicioPendiente] | / bloquearNuevaJornada() | Requiere_Service | external | Service pendiente impide una nueva jornada. |
| 04-T11 | En_Ruta_Operativa | fallaMecanicaCritica() | — | / registrarAveria() | Varado_En_Averia | external | Avería crítica en ruta → varado y alerta de transbordo. |
| 04-T12 | Varado_En_Averia | confirmarRemolque() | [unidadRecibidaEnTaller] | / registrarIngresoTaller() | En_Taller_Mantenimiento | external | Remolque confirmado → taller. |
| 04-T13 | Requiere_Service | iniciarMantenimiento() | [tallerAutorizado] | / registrarOrdenServicio() | En_Taller_Mantenimiento | external | Inicio del mantenimiento autorizado. |
| 04-T14 | En_Taller_Mantenimiento | finalizarMantenimiento() | [pruebaTecnicaAprobada] | / actualizarKilometrajeServicio() | Estacionado_Fuera_De_Servicio | external | Prueba técnica aprobada |
| 04-T15 | Estacionado_Fuera_De_Servicio | detectarServicioVencido() | [servicioPendiente] | / bloquearDespacho() | Requiere_Service | external | Telemetría detecta service vencido en base. |
| 04-T16 | Disponible_En_Base | detectarServicioVencido() | [servicioPendiente] | / bloquearDespacho() | Requiere_Service | external | Telemetría detecta service vencido antes de asignar ruta. |
| 04-T17 | En_Carga_Mercancia | detectarServicioVencido() | [servicioPendiente] | / bloquearDespacho() | Requiere_Service | external | Telemetría detecta service vencido durante la carga. |
| 04-T18 | En_Ruta_Operativa | detectarServicioVencido() | [!fallaCritica] | / marcarServicioParaRegreso() | En_Ruta_Operativa | internal | No detiene bruscamente la ruta por mantenimiento preventivo |

## 05 CasilleroInteligente

| ID | Estado origen | Evento | Guarda | Efecto | Estado destino | Tipo | Justificación |
|---|---|---|---|---|---|---|---|
| 05-T01 | Initial | — | — | — | En_Operacion::Vacio_Disponible | external | El compartimento arranca vacío y disponible. |
| 05-T02 | En_Operacion::Vacio_Disponible | reservarCasillero() | [reservaValida && hardwareSano] | / persistirReservaYFechaLimite() | En_Operacion::Reservado_Para_Entrega | external | Reserva solo con hardware sano |
| 05-T03 | En_Operacion::Reservado_Para_Entrega | at(fechaLimiteReserva) | — | / liberarReservaVencida() | En_Operacion::Vacio_Disponible | external | Si el repartidor no llega, la reserva se libera |
| 05-T04 | En_Operacion::Reservado_Para_Entrega | escanearOrden() | [repartidorAutorizado && reservaCoincidente] | / persistirOperacionCarga() | En_Operacion::Apertura_Pendiente_Carga | external | Repartidor autorizado y reserva coincidente solicitan apertura. |
| 05-T05 | En_Operacion::Ocupado_Esperando_Retiro_Cliente | validarCodigoRetiro() | [codigoValido && ahora < fechaLimiteRetiro] | / persistirOperacionRetiro() | En_Operacion::Apertura_Pendiente_Retiro | external | Código válido y vigente |
| 05-T06 | En_Operacion::Vencido_Pendiente_Recoleccion | autorizarRecoleccion() | [recolectorAutorizado] | / persistirOperacionRecoleccion() | En_Operacion::Apertura_Pendiente_Recoleccion | external | Solo personal autorizado recolecta un vencido. |
| 05-T07 | En_Operacion::Apertura_Pendiente_Carga | confirmarApertura() | [sensorPuertaAbierta] | / registrarAperturaConfirmada() | En_Operacion::Puerta_Abierta_Cargando | external | El sensor confirma la apertura |
| 05-T08 | En_Operacion::Apertura_Pendiente_Retiro | confirmarApertura() | [sensorPuertaAbierta] | / registrarAperturaConfirmada() | En_Operacion::Puerta_Abierta_Retirando | external | El sensor confirma la apertura para el retiro. |
| 05-T09 | En_Operacion::Apertura_Pendiente_Recoleccion | confirmarApertura() | [sensorPuertaAbierta] | / registrarAperturaConfirmada() | En_Operacion::Puerta_Abierta_Recolectando | external | El sensor confirma la apertura para la recolección. |
| 05-T10 | En_Operacion::Puerta_Abierta_Cargando | confirmarCierre() | [lecturaConfiable && puertaCerrada && cerraduraTrabada && peso > 0] | / confirmarDepositoYFechaLimite() | En_Operacion::Ocupado_Esperando_Retiro_Cliente | external | Custodia segura: cerrada, trabada y con peso → se notifica al cliente. |
| 05-T11 | En_Operacion::Puerta_Abierta_Cargando | confirmarCierre() | [lecturaConfiable && puertaCerrada && cerraduraTrabada && peso == 0] | / registrarCargaNoRealizada() | En_Operacion::Reservado_Para_Entrega | external | Cierre sin paquete: la entrega sigue pendiente. |
| 05-T12 | En_Operacion::Puerta_Abierta_Retirando | confirmarCierre() | [lecturaConfiable && puertaCerrada && cerraduraTrabada && peso == 0] | / cerrarRetiroYLiberarCasillero() | En_Operacion::Vacio_Disponible | external | Retiro completo, peso cero → compartimento libre. |
| 05-T13 | En_Operacion::Puerta_Abierta_Retirando | confirmarCierre() | [lecturaConfiable && puertaCerrada && cerraduraTrabada && peso > 0 && ahora < fechaLimiteRetiro] | / regenerarCodigoConPlazoOriginal() | En_Operacion::Ocupado_Esperando_Retiro_Cliente | external | Cerró sin retirar dentro del plazo: conserva ocupación y plazo original. |
| 05-T14 | En_Operacion::Puerta_Abierta_Retirando | confirmarCierre() | [lecturaConfiable && puertaCerrada && cerraduraTrabada && peso > 0 && ahora >= fechaLimiteRetiro] | / solicitarRecoleccion() | En_Operacion::Vencido_Pendiente_Recoleccion | external | Cerró sin retirar con el plazo vencido → vencido. |
| 05-T15 | En_Operacion::Puerta_Abierta_Recolectando | confirmarCierre() | [lecturaConfiable && puertaCerrada && cerraduraTrabada && peso == 0] | / confirmarTransferenciaARecolector() | En_Operacion::Vacio_Disponible | external | Recolección completa → compartimento libre. |
| 05-T16 | En_Operacion::Puerta_Abierta_Recolectando | confirmarCierre() | [lecturaConfiable && puertaCerrada && cerraduraTrabada && peso > 0] | / registrarRecoleccionIncompleta() | En_Operacion::Vencido_Pendiente_Recoleccion | external | Recolección incompleta → sigue vencido. |
| 05-T17 | En_Operacion::Ocupado_Esperando_Retiro_Cliente | after(72 h) | [ahora >= fechaLimiteRetiro] | / invalidarCodigoYSolicitarRecoleccion() | En_Operacion::Vencido_Pendiente_Recoleccion | external | Sin retiro en 72 h → vencido |
| 05-T18 | En_Operacion::Ocupado_Esperando_Retiro_Cliente | at(fechaLimiteRetiro) | — | / invalidarCodigoYSolicitarRecoleccion() | En_Operacion::Vencido_Pendiente_Recoleccion | external | El vencimiento absoluto conservado evita reiniciar las 72 h al recuperar energía o cerrar una puerta sin retirar el paquete. |
| 05-T19 | En_Operacion::Apertura_Pendiente_Carga | after(timeoutApertura) | — | / registrarAperturaNoConfirmada() | Fuera_De_Servicio_Mantenimiento | external | La puerta no confirmó la apertura → falla de hardware |
| 05-T20 | En_Operacion::Apertura_Pendiente_Retiro | after(timeoutApertura) | — | / registrarAperturaNoConfirmada() | Fuera_De_Servicio_Mantenimiento | external | La puerta no confirmó la apertura para el retiro. |
| 05-T21 | En_Operacion::Apertura_Pendiente_Recoleccion | after(timeoutApertura) | — | / registrarAperturaNoConfirmada() | Fuera_De_Servicio_Mantenimiento | external | La puerta no confirmó la apertura para la recolección. |
| 05-T22 | En_Operacion | detectarAperturaForzada() | [!comandoAutorizado] | / registrarViolacion() | Alarma_Violacion_Seguridad | external | Apertura sin comando digital → alarma, desde cualquier subestado operativo. |
| 05-T23 | En_Operacion | detectarFalloCerradura() | — | / registrarFalloHardware() | Fuera_De_Servicio_Mantenimiento | external | La cerradura no traba → fuera de servicio, desde cualquier subestado. |
| 05-T24 | En_Operacion | reiniciarControlador() | — | / recuperarOperacionPendiente() | En_Recuperacion | external | Se procesa al retornar la energía. No se supone que el dispositivo ejecute acciones mientras está apagado. |
| 05-T25 | Alarma_Violacion_Seguridad | autorizarRevision() | [seguridadAutoriza] | / registrarRevisionAutorizada() | En_Recuperacion | external | La alarma solo se libera con autorización de seguridad y pasa por recuperación. |
| 05-T26 | Fuera_De_Servicio_Mantenimiento | confirmarReparacion() | [tecnicoAutorizado && pruebaHardwareAprobada] | / registrarReparacion() | En_Recuperacion | external | Reparación probada → recuperación antes de volver a operar. |
| 05-T27 | En_Recuperacion | recibirLecturaSensores() | [lecturaConfiable] | / clasificarRecuperacion() | Choice C1 | external | Se clasifica el estado físico real contra lo persistido. |
| 05-T28 | Choice C1 | — | [recuperacion == 'CARGA_ABIERTA'] | / restaurarEstadoConPlazosPersistidos() | En_Operacion::Puerta_Abierta_Cargando | external | Carga abierta identificada → retoma el cierre seguro. |
| 05-T29 | Choice C1 | — | [recuperacion == 'OCUPADO_VIGENTE'] | / restaurarEstadoConPlazosPersistidos() | En_Operacion::Ocupado_Esperando_Retiro_Cliente | external | Ocupación válida → conserva su fecha límite original. |
| 05-T30 | Choice C1 | — | [recuperacion == 'OCUPADO_VENCIDO'] | / restaurarEstadoConPlazosPersistidos() | En_Operacion::Vencido_Pendiente_Recoleccion | external | Ocupación vencida permanece vencida. |
| 05-T31 | Choice C1 | — | [recuperacion == 'VACIO_LIBRE'] | / restaurarEstadoConPlazosPersistidos() | En_Operacion::Vacio_Disponible | external | Vacío sin obligaciones pendientes → disponible. |
| 05-T32 | Choice C1 | — | [recuperacion == 'VACIO_RESERVADO'] | / restaurarEstadoConPlazosPersistidos() | En_Operacion::Reservado_Para_Entrega | external | Vacío con reserva vigente → reservado. |
| 05-T33 | Choice C1 | — | [else] | / registrarInconsistenciaFisica() | Fuera_De_Servicio_Mantenimiento | external | Datos incoherentes → mantenimiento |
| 05-T34 | En_Operacion::Puerta_Abierta_Cargando | confirmarCierre() | [lecturaConfiable && puertaCerrada && !cerraduraTrabada] | / registrarFalloHardware() | Fuera_De_Servicio_Mantenimiento | external | Cierre sin traba exige mantenimiento; no libera la reserva ni el paquete. |
| 05-T35 | En_Operacion::Puerta_Abierta_Cargando | after(timeoutCierre) | — | / registrarCierreNoConfirmadoYAlertar() | Fuera_De_Servicio_Mantenimiento | external | Ausencia de cierre seguro bloquea el compartimento y conserva su custodia. |
| 05-T36 | En_Operacion::Puerta_Abierta_Retirando | confirmarCierre() | [lecturaConfiable && puertaCerrada && !cerraduraTrabada] | / registrarFalloHardware() | Fuera_De_Servicio_Mantenimiento | external | Cierre sin traba exige mantenimiento; no libera la reserva ni el paquete. |
| 05-T37 | En_Operacion::Puerta_Abierta_Retirando | after(timeoutCierre) | — | / registrarCierreNoConfirmadoYAlertar() | Fuera_De_Servicio_Mantenimiento | external | Ausencia de cierre seguro bloquea el compartimento y conserva su custodia. |
| 05-T38 | En_Operacion::Puerta_Abierta_Recolectando | confirmarCierre() | [lecturaConfiable && puertaCerrada && !cerraduraTrabada] | / registrarFalloHardware() | Fuera_De_Servicio_Mantenimiento | external | Cierre sin traba exige mantenimiento; no libera la reserva ni el paquete. |
| 05-T39 | En_Operacion::Puerta_Abierta_Recolectando | after(timeoutCierre) | — | / registrarCierreNoConfirmadoYAlertar() | Fuera_De_Servicio_Mantenimiento | external | Ausencia de cierre seguro bloquea el compartimento y conserva su custodia. |

## 06 TicketDeSoporte

| ID | Estado origen | Evento | Guarda | Efecto | Estado destino | Tipo | Justificación |
|---|---|---|---|---|---|---|---|
| 06-T01 | Initial | — | — | — | Registrado_En_Cola | external | El ticket nace en cola. |
| 06-T02 | Registrado_En_Cola | tomarTicket() | — | / asignarAgenteN1() | Asignado_Nivel_1 | external | Un agente N1 toma el ticket. |
| 06-T03 | Asignado_Nivel_1 | iniciarAnalisis() | — | / registrarInicioAtencion() | En_Analisis | external | El agente inicia el análisis. |
| 06-T04 | En_Analisis | solicitarInformacion() | — | / enviarSolicitudUsuario() | En_Espera_Respuesta_Usuario | external | El agente pide información adicional. |
| 06-T05 | En_Espera_Respuesta_Usuario | responderUsuario() | — | / adjuntarRespuesta() | En_Analisis | external | El usuario responde y el ticket vuelve a análisis. |
| 06-T06 | En_Analisis | resolverTicket() | — | / notificarSolucion() | Resuelto_Esperando_Confirmacion | external | El agente N1 propone solución. |
| 06-T07 | En_Analisis | escalar() | [complejidad == 'ALTA'] | / transferirANivel2() | Escalado_Nivel_2_Ingenieria | external | Complejidad técnica alta → escalar() a N2. |
| 06-T08 | Escalado_Nivel_2_Ingenieria | resolverTicket() | — | / notificarSolucion() | Resuelto_Esperando_Confirmacion | external | N2 propone solución. |
| 06-T09 | Resuelto_Esperando_Confirmacion | responderConfirmacion() | — | — | Choice C1 | external | La respuesta del usuario se clasifica en conforme / no conforme. |
| 06-T10 | Choice C1 | — | [!conforme] | / registrarObjecion() | Reabierto_En_Disputa | external | Usuario no conforme → reabierto en disputa. |
| 06-T11 | Resuelto_Esperando_Confirmacion | after(48h) | — | / cerrarAutomaticamente() | Cerrado_Por_Inactividad | external | Sin confirmación ni objeción en 48 h → cierre automático. |
| 06-T12 | En_Espera_Respuesta_Usuario | at(fechaLimiteRespuesta) | — | / notificarAbandono() | Cerrado_Sin_Solucion_Abandono | external | Calcular cinco días hábiles con calendario de negocio |
| 06-T13 | Reabierto_En_Disputa | reasignarTicket() | — | / priorizarTicket() | Asignado_Nivel_1 | external | El ticket reabierto vuelve a N1 con prioridad. |
| 06-T14 | Resuelto_Esperando_Confirmacion | at(fechaLimiteConfirmacion) | — | / cerrarAutomaticamente() | Cerrado_Por_Inactividad | external | Fecha límite absoluta del plazo de 48 h |
| 06-T15 | Choice C1 | — | [conforme] | / cerrarTicket() | Final | external | Usuario conforme → cierre. |
| 06-T16 | Cerrado_Sin_Solucion_Abandono | — | — | — | Final | external | Fin por abandono. |
| 06-T17 | Cerrado_Por_Inactividad | — | — | — | Final | external | Fin por inactividad. |

## 07 SolicitudDeDevolucion

| ID | Estado origen | Evento | Guarda | Efecto | Estado destino | Tipo | Justificación |
|---|---|---|---|---|---|---|---|
| 07-T01 | Initial | — | — | — | Solicitada_Por_Cliente | external | La solicitud nace del cliente. |
| 07-T02 | Solicitada_Por_Cliente | recibirEvidencias() | — | / validarFotosYRecibo() | En_Revision_Elegibilidad | external | Atención valida fotos y recibo. |
| 07-T03 | En_Revision_Elegibilidad | evaluarElegibilidad() | — | — | Choice C1 | external | Evaluación de la política de 30 días. |
| 07-T04 | Choice C1 | — | [diasEntregaASolicitud <= 30] | / notificarAprobacion() | Aprobada_Generando_Guia_Retorno | external | Dentro de 30 días → se genera la guía de retorno. |
| 07-T05 | Choice C1 | — | [diasEntregaASolicitud > 30] | / notificarRechazo() | Rechazada_Fuera_De_Politica | external | Pasados 30 días → rechazo. |
| 07-T06 | Aprobada_Generando_Guia_Retorno | recibirEnBodega() | — | / registrarIngreso() | Recibida_En_Inspeccion_Calidad | external | El paquete llega a bodega para inspección. |
| 07-T07 | Aprobada_Generando_Guia_Retorno | after(15 dias) | [!envioRetornoConfirmado] | / cancelarGuiaRetorno() | Cancelada_Por_No_Envio | external | Plazo adicional de 15 días heredado de Claude, no fijado por el PDF. Solo puede cancelar si el cliente todavía no ha despachado el retorno. |
| 07-T08 | Recibida_En_Inspeccion_Calidad | completarInspeccion() | — | — | Choice C2 | external | Resultado de la inspección física. |
| 07-T09 | Choice C2 | — | [estadoProducto == 'ORIGINAL'] | / registrarAprobacion() | Aprobada_Para_Reembolso | external | Producto en estado original → aprobado para reembolso. |
| 07-T10 | Choice C2 | — | [estadoProducto != 'ORIGINAL'] | / devolverProductoACliente() | Rechazada_Fraude_Garantia | external | Producto manipulado o falso → rechazo, devuelto sin dinero. |
| 07-T11 | Aprobada_Para_Reembolso | confirmarReembolso() | [confirmacionBancariaValida] | / registrarReembolsoConfirmado() | Liquidada_Cerrada | external | Solo la confirmación bancaria cierra: reembolso solicitado ≠ confirmado. |
| 07-T12 | Aprobada_Para_Reembolso | after(timeoutReembolso) | — | / registrarResultadoIncierto() | Reembolso_En_Conciliacion | external | Sin confirmación del banco → conciliación |
| 07-T13 | Reembolso_En_Conciliacion | confirmarReembolso() | [confirmacionBancariaValida] | / registrarReembolsoConfirmado() | Liquidada_Cerrada | external | La conciliación confirma el reembolso. |
| 07-T14 | Reembolso_En_Conciliacion | reintentarReembolso() | [falloDefinitivoSinAcreditacion && soporteAutoriza && reintentosReembolso < maxReintentosReembolso] | / incrementarReintentosYConservarClave() | Aprobada_Para_Reembolso | external | Límite configurable de reintentos. Agotado el límite, permanece bloqueado para conciliación/confirmación bancaria, sin crear más solicitudes de devolución. |
| 07-T15 | Aprobada_Generando_Guia_Retorno | confirmarEnvioRetorno() | [guiaValida] | / registrarEnvioRetorno() | Aprobada_Generando_Guia_Retorno | internal | Transición interna: registra el despacho del cliente sin reemitir la guía ni reiniciar el plazo de 15 días. |
| 07-T16 | Reembolso_En_Conciliacion | at(proximaFechaSeguimiento) | — | / alertarResponsableYReprogramarSeguimiento() | Reembolso_En_Conciliacion | internal | Alerta y rearma la fecha sin alterar el resultado ni repetir efectos financieros. |
| 07-T17 | Liquidada_Cerrada | — | — | — | Final | external | Fin natural: reembolso confirmado. |
| 07-T18 | Rechazada_Fuera_De_Politica | — | — | — | Final | external | Fin: fuera de política. |
| 07-T19 | Rechazada_Fraude_Garantia | — | — | — | Final | external | Fin: fraude de garantía. |
| 07-T20 | Cancelada_Por_No_Envio | — | — | — | Final | external | Fin: el cliente no envió el retorno. |

## 08 LoteDeInventario

| ID | Estado origen | Evento | Guarda | Efecto | Estado destino | Tipo | Justificación |
|---|---|---|---|---|---|---|---|
| 08-T01 | Initial | — | — | — | Recibido_En_Cuarentena | external | El lote entra al muelle en cuarentena. |
| 08-T02 | En_Almacen::Activo_En_Picking | descontarUnidades() | [cantidad > 0 && cantidad <= existencias] | / descontarStockAtomico() | Choice C2 | external | Descuento atómico validado |
| 08-T03 | Choice C2 | — | [existencias > 0] | / registrarSaldoDisponible() | En_Almacen::Activo_En_Picking | external | Quedan existencias → sigue en picking. |
| 08-T04 | En_Almacen::Aprobado_En_Ubicacion_Almacen | descontarUnidades() | [cantidad > 0 && cantidad <= existencias] | / descontarStockAtomico() | Choice C2 | external | Primer descuento desde la ubicación. |
| 08-T05 | Recibido_En_Cuarentena | completarControlCalidad() | — | — | Choice C1 | external | Resultado del control de calidad. |
| 08-T06 | Choice C1 | — | [resultadoQC == 'APROBADO'] | / asignarUbicacion() | En_Almacen::Aprobado_En_Ubicacion_Almacen | external | Control de calidad aprobado → ubicación en almacén. |
| 08-T07 | Choice C1 | — | [else] | / notificarProveedor() | Destruido_Decomisado | external | Todo resultado que no sea APROBADO se trata de forma conservadora |
| 08-T08 | En_Almacen | marcarMerma() | — | / registrarIncidente() | Bloqueado_Por_Siniestro | external | Incidente en almacén → marcarMerma() bloquea el lote, desde cualquier subestado. |
| 08-T09 | Bloqueado_Por_Siniestro | decomisarLote() | — | / emitirActaDestruccion() | Destruido_Decomisado | external | Desde el bloqueo, el único destino es el decomiso. |
| 08-T10 | En_Almacen | emitirRecall() | — | / bloquearVentas() | Inmovilizado_Por_Recall | external | Recall del proveedor inmoviliza el lote en almacén. |
| 08-T11 | Recibido_En_Cuarentena | emitirRecall() | — | / bloquearVentas() | Inmovilizado_Por_Recall | external | Recall también aplica durante la cuarentena. |
| 08-T12 | Choice C2 | — | [existencias == 0] | / liberarUbicacion() | Agotado | external | Existencias en cero → agotado en el mismo evento. |
| 08-T13 | Inmovilizado_Por_Recall | devolverAProveedor() | — | / generarNotaCredito() | Final | external | Devolución al proveedor con nota de crédito cierra el ciclo. |
| 08-T14 | Destruido_Decomisado | — | — | — | Final | external | Fin: lote destruido. |
| 08-T15 | Agotado | — | — | — | Final | external | Fin natural: existencias agotadas. |

## 09 CuentaDeConductor

| ID | Estado origen | Evento | Guarda | Efecto | Estado destino | Tipo | Justificación |
|---|---|---|---|---|---|---|---|
| 09-T01 | Initial | — | — | — | Registro_Incompleto | external | La cuenta nace con registro incompleto. |
| 09-T02 | Activo_Habilitado::Desconectado | conectarse() | — | / publicarDisponibilidad() | Activo_Habilitado::En_Linea_Disponible | external | El conductor se conecta. |
| 09-T03 | Activo_Habilitado::En_Linea_Disponible | desconectarse() | — | / retirarDeDespacho() | Activo_Habilitado::Desconectado | external | El conductor se desconecta. |
| 09-T04 | Registro_Incompleto | subirDocumentos() | [dni && licencia && antecedentes] | / enviarACompliance() | Documentacion_En_Validacion | external | DNI, licencia y antecedentes completos → validación. |
| 09-T05 | Documentacion_En_Validacion | rechazarDocumentos() | — | / notificarCorreccion() | Registro_Incompleto | external | Compliance rechaza: el conductor debe corregir. |
| 09-T06 | Documentacion_En_Validacion | aprobarDocumentos() | — | / habilitarCuenta() | Activo_Habilitado::Desconectado | external | Compliance verifica los documentos. |
| 09-T07 | Activo_Habilitado | evaluarDesempeno() | [!fraudeConfirmado && (calificacion < 4.2 \|\| quejasGraves >= 3)] | / notificarSuspension() | Suspendido_Por_Bajo_Desempeno | external | Calificación < 4.2 o 3 quejas graves → suspensión. |
| 09-T08 | Suspendido_Por_Bajo_Desempeno | completarReentrenamiento() | [cursoAprobado && complianceAutoriza && !fraudeConfirmado] | / reactivarCuenta() | Activo_Habilitado::Desconectado | external | Compliance resuelve el motivo de suspensión antes de reactivar |
| 09-T09 | Activo_Habilitado | detectarFraude() | [fraudeConfirmado && (fakeGPS \|\| sustraccionPaquetes)] | / vetarConductor() | Expulsado_Permanente | external | Fake GPS o sustracción confirmados → expulsión irreversible. |
| 09-T10 | Suspendido_Por_Bajo_Desempeno | detectarFraude() | [fraudeConfirmado && (fakeGPS \|\| sustraccionPaquetes)] | / vetarConductor() | Expulsado_Permanente | external | El fraude confirmado también expulsa a un suspendido. |
| 09-T11 | Registro_Incompleto | at(proximaFechaSeguimiento) | — | / alertarResponsableYReprogramarSeguimiento() | Registro_Incompleto | internal | Alerta y rearma la fecha sin alterar el resultado ni repetir efectos financieros. |
| 09-T12 | Activo_Habilitado | solicitarBaja() | [identidadVerificada && !paquetesPendientes && !obligacionesOperativasPendientes && !fraudeConfirmado] | / registrarBajaVoluntaria() | Dado_De_Baja | external | Baja verificada sin custodia ni obligaciones pendientes. |
| 09-T13 | Expulsado_Permanente | — | — | — | Final | external | Fin irreversible: conductor vetado. |
| 09-T14 | Dado_De_Baja | — | — | — | Final | external | Fin contractual con historial conservado. |

## 10 DisputaBancaria

| ID | Estado origen | Evento | Guarda | Efecto | Estado destino | Tipo | Justificación |
|---|---|---|---|---|---|---|---|
| 10-T01 | Initial | — | — | — | Notificada_Por_Red_Bancaria | external | La disputa nace con la notificación de la red bancaria. |
| 10-T02 | Notificada_Por_Red_Bancaria | registrarDisputa() | — | / abrirExpediente() | En_Recoleccion_De_Evidencias | external | Se retienen fondos y se abre el expediente. |
| 10-T03 | En_Recoleccion_De_Evidencias | enviarEvidencias() | [fotos && gps && firma && ahora < fechaLimiteEvidencias] | / transmitirAlEmisor() | Evidencias_Presentadas_Al_Emisor | external | Fotos, GPS y firma completas, dentro del plazo. |
| 10-T04 | Evidencias_Presentadas_Al_Emisor | confirmarRecepcionEmisor() | — | / iniciarPlazoArbitraje() | En_Arbitraje_Bancario | external | El emisor confirma recepción → arbitraje. |
| 10-T05 | En_Arbitraje_Bancario | recibirFallo() | [firmaValida && (fallo == 'A_FAVOR_EMPRESA' \|\| fallo == 'A_FAVOR_CLIENTE')] | / guardarFalloVerificado() | Choice C1 | external | Solo se acepta un fallo firmado con resultado contemplado. |
| 10-T06 | Choice C1 | — | [fallo == 'A_FAVOR_EMPRESA'] | / liberarFondos() | Ganada_Fondos_Liberados | external | Fallo a favor de la empresa → fondos liberados. |
| 10-T07 | Choice C1 | — | [fallo == 'A_FAVOR_CLIENTE'] | / aplicarContracargo() | Perdida_Con_Penalizacion | external | Fallo a favor del cliente → contracargo. |
| 10-T08 | En_Recoleccion_De_Evidencias | after(7 dias) | — | / registrarPerdidaPorPlazo() | Perdida_Con_Penalizacion | external | Sin evidencias en 7 días → pérdida). |
| 10-T09 | Notificada_Por_Red_Bancaria | allanarse() | — | / reembolsarTarjetahabiente() | Aceptada_Sin_Disputa | external | allanarse(): el monto no justifica litigar. |
| 10-T10 | En_Recoleccion_De_Evidencias | allanarse() | — | / reembolsarTarjetahabiente() | Aceptada_Sin_Disputa | external | allanarse() también durante la recolección de evidencias. |
| 10-T11 | En_Recoleccion_De_Evidencias | at(fechaLimiteEvidencias) | — | / registrarPerdidaPorPlazo() | Perdida_Con_Penalizacion | external | Fecha límite absoluta de evidencias |
| 10-T12 | En_Arbitraje_Bancario | after(45 dias) | — | / registrarPlazoExcedido() | En_Seguimiento_Plazo_Excedido | external | El silencio del banco no implica victoria ni derrota. Estado añadido como decisión conservadora. |
| 10-T13 | En_Arbitraje_Bancario | at(fechaLimiteArbitraje) | — | / registrarPlazoExcedido() | En_Seguimiento_Plazo_Excedido | external | Fecha límite absoluta del arbitraje. |
| 10-T14 | En_Seguimiento_Plazo_Excedido | recibirFallo() | [firmaValida && (fallo == 'A_FAVOR_EMPRESA' \|\| fallo == 'A_FAVOR_CLIENTE')] | / guardarFalloVerificado() | Choice C1 | external | Un fallo tardío se procesa igual que uno a tiempo. |
| 10-T15 | Evidencias_Presentadas_Al_Emisor | at(proximaFechaSeguimiento) | — | / alertarResponsableYReprogramarSeguimiento() | Evidencias_Presentadas_Al_Emisor | internal | Alerta y rearma la fecha sin alterar el resultado ni repetir efectos financieros. |
| 10-T16 | En_Seguimiento_Plazo_Excedido | at(proximaFechaSeguimiento) | — | / alertarResponsableYReprogramarSeguimiento() | En_Seguimiento_Plazo_Excedido | internal | Alerta y rearma la fecha sin alterar el resultado ni repetir efectos financieros. |
| 10-T17 | Aceptada_Sin_Disputa | — | — | — | Final | external | Fin: aceptada sin disputa. |
| 10-T18 | Ganada_Fondos_Liberados | — | — | — | Final | external | Fin: ganada. |
| 10-T19 | Perdida_Con_Penalizacion | — | — | — | Final | external | Fin: perdida. |
