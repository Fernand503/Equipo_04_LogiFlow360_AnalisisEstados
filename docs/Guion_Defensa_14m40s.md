# Guion de defensa de LogiFlow 360

Duración objetivo: **14 minutos y 40 segundos**. Es una agenda de ensayo; el video final debe durar entre 12 y 15 minutos. Mantener cámaras encendidas, audio claro y vestimenta profesional. Las indicaciones de pantalla no se leen.

| Rol | Expositor |
|---|---|
| 1 | ANDERSON ERNESTO CASTILLO NAVARRETE |
| 2 | CARLOS DANIEL RIVAS GARCIA |
| 3 | JOSÉ FERNANDO DÍAZ DEL CID |
| 4 | ANTHONY ENRIQUE ALVARENGA RIVAS |
| 5 | DIEGO ENRIQUE VÁSQUEZ SARACAY |

Abrir `LogiFlow360_StateModels.mdj` en StarUML. En el explorador, cada entidad contiene su máquina `SM_` y su diagrama `SMD_`. El paquete 11 contiene el diagrama de clases. Preparar también las matrices, el informe y el código. Ajustar el zoom para leer el sector que se explica; usar la vista completa solo para situar al público.

## 00:00 a 00:30 Rol 5 Presentación

Pantalla: explorador del modelo con los once paquetes.

> Buenos días. Somos el equipo 04 y presentamos la arquitectura de estados de LogiFlow 360. Anderson lidera arquitectura; Carlos, reglas de negocio; José Fernando, documentación y calidad; Anthony, integración y persistencia; y yo, Diego, la defensa de negocio. Mostraremos cómo el diseño protege las operaciones y el dinero de la plataforma.

## 00:30 a 02:00 Rol 1 Problema y arquitectura

Pantalla: los diez diagramas en el explorador; luego OrdenDeCompra.

> El caso describe una plataforma con más de quinientas mil operaciones diarias. Con esa escala, un estado incoherente puede convertirse en una pérdida repetida muchas veces. Por ejemplo, una orden puede aparecer cancelada mientras el almacén sigue preparando el paquete, o un pago puede enviarse otra vez porque la primera respuesta tardó en llegar.
>
> Si representamos todo con indicadores independientes, como pagado, cancelado o enviado, también permitimos combinaciones contradictorias. Nuestro modelo establece situaciones válidas y las condiciones para pasar de una a otra. Cada flecha responde tres preguntas: qué ocurrió, qué condición debe cumplirse y qué efecto se solicita.
>
> Organizamos diez máquinas independientes, una por entidad. La orden describe el compromiso comercial; el pago, su resultado financiero; y el paquete, la custodia física. No hacemos que una sola máquina controle todo el negocio. Los servicios intercambian eventos verificados para coordinar sus respectivos ciclos.
>
> Además del recorrido esperado, modelamos cancelaciones, reintentos, vencimientos y recuperación. El objetivo es que los desarrolladores y quienes prueban el sistema compartan el mismo contrato. Ahora veremos ese contrato aplicado a una compra.

## 02:00 a 04:00 Rol 1 OrdenDeCompra

Pantalla: `SMD_OrdenDeCompra`. Señalar el checkout, la autorización, la retención por stock y las cancelaciones.

> La orden nace como Borrador_En_Carrito. El checkout solo habilita la espera de pago si el carrito es válido y existe una reserva confirmada. Al entrar se conserva una fecha límite; no basta con iniciar un contador que desaparezca cuando reinicia el servidor.
>
> Si la autorización válida llega dentro del plazo y la reserva sigue vigente, pasamos al procesamiento en almacén. Si pasan treinta minutos sin autorización, la orden se cancela por timeout y se libera el inventario. Un pago tardío no revive esa orden: exige una resolución financiera separada.
>
> Aquí se ven after, que expresa la duración, y at, que representa el vencimiento absoluto persistido. Pueden producir avisos equivalentes, por lo que el backend debe deduplicarlos y volver a comprobar el estado antes de aplicar el cambio.
>
> En almacén, la guarda exige stock disponible y ausencia de una cancelación confirmada. Si ocurre un quiebre de inventario, la orden queda retenida hasta cinco días hábiles. Ese plazo requiere un calendario de negocio; no lo reemplazamos por ciento veinte horas sin considerar fines de semana o festivos.
>
> El cliente puede cancelar antes del empaquetado. Después de Empacada ya no existe esa transición. La entrega se completa con evidencia válida. También distinguimos registrar una obligación de reembolso de afirmar que el banco ya acreditó el dinero. Solicitar una compensación es una acción; confirmar su resultado es otro evento.
>
> Para controlar la carrera entre cancelar y empaquetar, el modelo se implementa junto con un control de versión persistido. Solo un cambio puede ganar sobre la misma versión. El siguiente bloque explica por qué esa disciplina también es necesaria al cobrar.

## 04:00 a 06:30 Rol 2 TransaccionDePago

Pantalla: `SMD_TransaccionDePago`. Ampliar antifraude y Choice, los reintentos y la conciliación.

> La transacción pasa primero por análisis antifraude. El scoring válido llega a una decisión con dos condiciones complementarias: riesgo menor al umbral o riesgo igual o mayor. Así evitamos que el mismo dato active dos destinos distintos o quede sin una decisión prevista.
>
> En el caso de riesgo bajo enviamos el pago a la pasarela. La respuesta se acepta cuando su firma y su correlación son válidas. El modelo distingue aprobación, autenticación reforzada, fondos insuficientes, error del emisor y un resultado desconocido que requiere conciliación.
>
> El desafío 3D Secure no representa otro cobro: completa la autenticación del intento existente. Si falla la red o se agota el tiempo de respuesta, no suponemos que el banco rechazó la operación. Puede haber autorizado aunque no recibamos su respuesta. Por eso consultamos y conciliamos antes de permitir una nueva solicitud.
>
> Adoptamos tres envíos totales: el inicial y hasta dos reintentos manuales. Cada envío incrementa el contador. Consultar una operación incierta no lo incrementa ni genera un cargo. Cuando el tercer resultado confirmado es de rechazo, una transición automática lleva a Fallida_Definitiva, sin pedir un cuarto clic al cliente.
>
> Si la conciliación no resuelve la incertidumbre, entramos en revisión manual. Hay un responsable y una próxima fecha de seguimiento persistida. El seguimiento es interno: alerta y reprograma sin salir y volver a entrar al estado, y sin repetir efectos financieros.
>
> También separamos autorización de liquidación. Autorizada no significa que el dinero ya esté depositado. El lote nocturno solicita la liquidación y la confirmación bancaria permite llegar a Liquidada_Depositada. Ante un resultado incierto, volvemos a conciliar.
>
> Estas reglas son útiles porque cada evento se evalúa contra el estado actual y la evidencia del servidor. El diagrama no verifica por sí mismo una firma digital ni autentica una API; define qué debe comprobar la implementación. El siguiente integrante mostrará cómo lo volvemos verificable en el paquete físico.

## 06:30 a 08:00 Rol 3 Matrices y PaqueteFisico

Pantalla: `SMD_PaqueteFisico` y la matriz 03. Mostrar entrega, tercera ausencia y recuperación.

> Nuestra documentación enlaza cada regla con una transición, una fila de matriz y un resultado esperado. Las diez matrices contienen las doscientas diecinueve transiciones del modelo; las justificaciones también están en su campo Documentation.
>
> Primer caso: desde Recibido_En_Hub_Origen no existe confirmarEntrega. La única transición logística siguiente inicia la clasificación. La entrega válida sale de En_Camino_A_Entrega y requiere actor autorizado y evidencia.
>
> Segundo caso: cada ausencia incrementa el contador y entra a Entrega_Fallida_Ausente. Con menos de tres intentos, se programa otra visita; con tres, se ordena el retorno. La recepción confirmada en el centro cierra ese recorrido.
>
> Tercer caso: encontrar un paquete extraviado no demuestra que ya llegó al almacén. Por eso usamos Recuperado_Pendiente_Recepcion. Un escaneo físico verificado permite decidir si reingresa por origen o destino; no lo trasladamos automáticamente al hub de destino.
>
> El verificador pasó doscientas cuarenta y ocho comprobaciones, incluidas cuarenta y siete simulaciones seleccionadas. Eso comprueba estructura y recorridos concretos; no garantiza todas las combinaciones de guardas ni sustituye las pruebas de integraciones reales.

## 08:00 a 10:00 Rol 5 CasilleroInteligente

Pantalla: `SMD_CasilleroInteligente`. Mostrar apertura pendiente, carga, vencimiento y mantenimiento.

> El casillero muestra dónde el software debe respetar la realidad física. Enviar un comando para abrir no prueba que la puerta se abrió. Por eso existe Apertura_Pendiente_Carga y esperamos la confirmación del sensor antes de pasar a Puerta_Abierta_Cargando.
>
> Para confirmar la ocupación necesitamos una lectura confiable, la puerta cerrada, la cerradura trabada y peso positivo. Si se cierra sin peso, la entrega no está confirmada. Si se cierra pero no queda trabada, pasamos directamente a mantenimiento. El mismo control existe durante el retiro del cliente y la recolección del repartidor.
>
> Las tres fases de puerta abierta también tienen un timeout de cierre. Si no llega una confirmación segura, bloqueamos el compartimento y alertamos. No lo declaramos vacío ni liberamos su paquete solo porque pasó el tiempo. Así conservamos la custodia mientras se resuelve el problema físico.
>
> El cliente tiene setenta y dos horas para retirar. Al vencer, invalidamos el código y solicitamos recolección. La fecha absoluta se conserva: abrir y cerrar sin retirar, o reiniciar el controlador, no regala otras setenta y dos horas.
>
> Una apertura forzada sin comando previo activa la alarma de seguridad. Es una contingencia distinta de una cerradura averiada. En ambos casos necesitamos una recuperación verificada antes de reasignar el espacio.
>
> Para el negocio, estas decisiones evitan que un casillero inseguro siga recibiendo paquetes y que uno ocupado quede retenido indefinidamente. En el cierre responderemos qué ocurre ante un corte eléctrico. Primero veremos cómo se programa y audita este contrato.

## 10:00 a 12:30 Rol 4 Patrón State y persistencia

Pantalla 1: `CD_PatronState_PaqueteFisico`. Pantalla 2: Java. Pantalla 3: DDL y función SQL.

> PaqueteFisico es el Context del patrón State: conserva su estado actual y delega cada evento al objeto que lo representa. EstadoPaquete define los eventos y los rechaza por defecto con TransicionInvalidaException. Cada clase concreta habilita los que le corresponden.
>
> RecibidoEnHubOrigen permite iniciar la clasificación, pero no confirma una entrega. EnCaminoAEntrega sí permite entregarla con evidencia válida. BajoCustodia reúne las contingencias heredadas de siniestro y extravío. El ejemplo también implementa recuperación, recepción física, retorno y los cierres automáticos.
>
> La demostración de Java pasó veintiocho comprobaciones. Incluye un evento duplicado que no incrementa dos veces los intentos, un identificador reutilizado con otro contenido que se rechaza y una entrega prematura que conserva el estado. La memoria de resultados es local al objeto y se pierde al reiniciar; por eso mostramos la persistencia por separado.
>
> En la base de datos, el catálogo estado pertenece a un tipo de entidad. Las claves foráneas compuestas impiden colocar el estado de un casillero en un paquete. El historial registra origen, destino, evento, responsable, fecha, versión y payload JSON. Los intentos rechazados se guardan aparte.
>
> La función valida las reglas implementadas y actualiza el paquete con una versión esperada. El resultado de ese UPDATE es la única fuente del historial aceptado. Si no cambió ninguna fila, tampoco se crea un historial ni una notificación como si hubiera ocurrido el cambio.
>
> El resultado del eventId se conserva globalmente. Una repetición idéntica devuelve el resultado anterior; usar el mismo identificador para otra petición es un error. Estado, historial, resultado y outbox se confirman en una transacción local. Después, un worker entrega el efecto externo con una clave idempotente. No afirmamos que exista una única transacción entre nuestra base, el banco y la cerradura.
>
> SQL pasó dieciséis comprobaciones sobre PostgreSQL. El ejemplo ejecutable cubre dos eventos del paquete; el diseño completo requiere implementar las otras reglas en sus servicios. Con eso pasamos a las preguntas del Product Owner.

## 12:30 a 13:10 Rol 1 Pregunta sobre inversión

> La primera pregunta es qué gana el negocio invirtiendo tres semanas en modelar en lugar de empezar a programar directamente.
>
> Gana un contrato común para construir y probar las reglas que protegen dinero y custodia. Corregir aquí una carrera entre cancelar y empaquetar evita replicar ese error en varios servicios. También permite revisar con el Product Owner qué debe ocurrir ante un timeout o una operación incierta antes de implementarlo. El retorno esperado es menos retrabajo e incidentes; no inventamos una cifra de ahorro sin datos reales de costos y frecuencia de fallos.

## 13:10 a 13:55 Rol 2 Pregunta sobre una entrega fraudulenta

> La segunda pregunta plantea que alguien intenta marcar como entregado un paquete que está en el hub de origen.
>
> El servidor consulta el estado persistido y busca una transición habilitada para ese evento. Desde Recibido_En_Hub_Origen no existe confirmarEntrega, por lo que rechaza la petición, conserva el estado y registra el intento. Además exige identidad, permisos, evidencia y versión válidos. No confía en el estado que envíe el cliente. La máquina define el contrato y el backend lo aplica; la notación UML por sí sola no detiene un ataque. Esta situación está incluida en las pruebas de Java y en la estrategia de auditoría.

## 13:55 a 14:40 Rol 5 Pregunta sobre el corte eléctrico y cierre

Pantalla: reiniciarControlador, En_Recuperacion y su Choice de sensores.

> La tercera pregunta es qué pasa si se corta la energía durante Puerta_Abierta_Cargando.
>
> Al volver la energía, el controlador entra a En_Recuperacion y contrasta el último estado y vencimiento persistidos con las lecturas físicas. No supone que quedó vacío ni que la carga terminó. Si la puerta sigue abierta y las lecturas son confiables, recupera la fase de carga; si confirman ocupación segura, aplica el resultado correspondiente y conserva el plazo. Una lectura incoherente bloquea el casillero y requiere mantenimiento. La custodia y los comandos pendientes deben reconciliarse antes de volver a operar.
>
> Concluimos que cada cambio debe estar permitido, verificado y registrado. Gracias por su atención.

## Ensayo y publicación

- Realizar un ensayo con cronómetro. Ajustar pausas y navegación para terminar cerca de 14:40 y dentro del límite de 12 a 15 minutos.
- No leer tablas enteras. Señalar la flecha o guarda que sostiene cada explicación.
- Todos deben intervenir con su rol y aparecer en cámara. Mantener los cambios de pantalla preparados.
- Sustituir los nombres de ejemplo, publicar el video, probar el enlace sin iniciar sesión y actualizar el README con los tiempos reales.
