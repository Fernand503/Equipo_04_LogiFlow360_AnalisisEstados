# Estado de la entrega

El paquete integra diez máquinas, 219 transiciones documentadas y un diagrama de clases del patrón State. Incluye el informe de 25 páginas, once PNG exportados por StarUML, matrices regenerables, ejemplo Java, DDL PostgreSQL y pruebas reproducibles.

| Verificación ejecutada | Resultado | Evidencia |
|---|---|---|
| Estructura del modelo y simulaciones seleccionadas | 248/248; 47 simulaciones | `qa/Verificacion_Rol2.json` |
| Patrón State en Java | 28/28 | `java/src/logiflow/paquete/PruebasPatronState.java` |
| Persistencia PostgreSQL | 16/16 en PostgreSQL 18.6 mediante PGlite 0.5.10 | `qa/Verificacion_SQL.json` |
| Apertura y exportación nativas | Once diagramas exportados por StarUML | `diagramas/` |

La verificación no certifica integraciones bancarias, sensores reales ni concurrencia distribuida. La alcanzabilidad es topológica. Las guardas representan condiciones que el backend debe evaluar con información confiable.

## Datos que el equipo debe completar

- En la portada: docente, nombres de los cinco integrantes, asignación real de roles y porcentajes que sumen 100 %. No se asignan porcentajes sin conocer la participación efectiva.
- Grabar la defensa entre 12 y 15 minutos, con todos los integrantes, cámaras encendidas y StarUML visible.
- Publicar el video con visualización pública habilitada. Colocar el enlace directo y el minutaje real en el punto 3 del README.

La portada conserva espacios para esos datos. El README indica expresamente que el video está pendiente. El repositorio aún no debe presentarse como entrega terminada.

## Decisiones de la revisión

| Observación | Decisión aplicada |
|---|---|
| QA 01 y 02 | Retiradas: las dos transiciones ya eran internas. |
| QA 03 | Un hallazgo lleva a Recuperado_Pendiente_Recepcion. Un escaneo físico verificado decide origen o destino mediante Choice. |
| QA 04 | Cierre sin traba y timeout en las tres fases de puerta abierta llevan a mantenimiento conservando custodia. |
| QA 05 | Seguimientos internos con responsable y próxima fecha; no inventan resultados financieros. |
| QA 06 | Baja voluntaria verificada sin paquetes ni obligaciones pendientes. |
| QA 07 | Las 219 transiciones tienen Documentation. |
| QA 08 | after() expresa la duración y at() conserva el vencimiento persistido; el backend deduplica las notificaciones. |

## Reproducir la verificación

Desde la raíz del repositorio, con Python 3:

```text
python qa/verificar_modelo.py
python qa/generar_matrices.py
```

Con JDK 9 o posterior, desde `java/`:

```text
javac -encoding UTF-8 -d out src/logiflow/paquete/*.java
java -cp out logiflow.paquete.PruebasPatronState
java -cp out logiflow.paquete.DemoPatronState
```

En una base PostgreSQL vacía, ejecutar primero `sql/auditoria_estados.sql` y luego `sql/ejemplo_transicion.sql`. La función implementa únicamente iniciarClasificacion y confirmarEntrega; el catálogo de ejemplo es un subconjunto de PaqueteFisico.

Para repetir la prueba automatizada local con Node.js:

```text
npm install --no-save @electric-sql/pglite@0.5.10
node qa/probar_sql.mjs
```

Los booleanos de autorización y evidencia del ejemplo provienen de verificaciones del servidor. El historial, estado actual, resultado del evento y outbox se confirman en la misma transacción local. El efecto externo se entrega después; el esquema no crea una transacción global con bancos o cerraduras.
