package logiflow.paquete;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/** Context. Los booleanos representan verificaciones confiables del backend.
 * Idempotencia local al objeto; SQL muestra la alternativa persistente.
 * No invoca sensores, transportistas ni servicios financieros reales. */
public class PaqueteFisico {
    private final String codigoRastreo;
    private EstadoPaquete estado = new ManifiestoCreado();
    private int intentosEntrega;
    private boolean cicloCerrado;
    private final Map<String, Resultado> resultadoPorEventId = new HashMap<>();
    private static final class Resultado {
        final String solicitud;
        final TransicionInvalidaException rechazo;
        Resultado(String solicitud, TransicionInvalidaException rechazo) { this.solicitud=solicitud;this.rechazo=rechazo; }
    }
    public PaqueteFisico(String codigoRastreo) { this.codigoRastreo=Objects.requireNonNull(codigoRastreo); }
    public void escanearRecepcion(String id, boolean etiqueta) {
        procesar(id,"escanearRecepcion()",""+etiqueta,()->estado.escanearRecepcion(this,etiqueta));
    }
    public void iniciarClasificacion(String id, boolean actor) {
        procesar(id,"iniciarClasificacion()",""+actor,()->{autorizar(actor,"iniciarClasificacion()");estado.iniciarClasificacion(this);});
    }
    public void confirmarSalidaHub(String id, boolean actor) {
        procesar(id,"confirmarSalidaHub()",""+actor,()->{autorizar(actor,"confirmarSalidaHub()");estado.confirmarSalidaHub(this);});
    }
    public void escanearLlegadaDestino(String id, boolean actor) {
        procesar(id,"escanearLlegadaDestino()",""+actor,()->{autorizar(actor,"escanearLlegadaDestino()");estado.escanearLlegadaDestino(this);});
    }
    public void asignarRuta(String id, boolean actor) {
        procesar(id,"asignarRuta()",""+actor,()->{autorizar(actor,"asignarRuta()");estado.asignarRuta(this);});
    }
    public void confirmarSalidaRuta(String id, boolean actor) {
        procesar(id,"confirmarSalidaRuta()",""+actor,()->{autorizar(actor,"confirmarSalidaRuta()");estado.confirmarSalidaRuta(this);});
    }
    public void confirmarEntrega(String id, boolean actor, boolean evidencia) {
        procesar(id,"confirmarEntrega()",actor+":"+evidencia,()->{autorizar(actor,"confirmarEntrega()");estado.confirmarEntrega(this,evidencia);});
    }
    public void reportarAusencia(String id) { procesar(id,"reportarAusencia()","",()->estado.reportarAusencia(this)); }
    public void confirmarRetorno(String id, boolean recepcion) { procesar(id,"confirmarRetorno()",""+recepcion,()->estado.confirmarRetorno(this,recepcion)); }
    public void reportarSiniestro(String id, boolean reporte) { procesar(id,"reportarSiniestro()",""+reporte,()->estado.reportarSiniestro(this,reporte)); }
    public void reportarExtravio(String id, boolean reporte) { procesar(id,"reportarExtravio()",""+reporte,()->estado.reportarExtravio(this,reporte)); }
    public void cerrarInvestigacion(String id, boolean supervisor, boolean recuperable) {
        procesar(id,"cerrarInvestigacion()",supervisor+":"+recuperable,()->estado.cerrarInvestigacion(this,supervisor,recuperable));
    }
    public void confirmarHallazgo(String id, boolean supervisor, boolean identidad) {
        procesar(id,"confirmarHallazgo()",supervisor+":"+identidad,()->estado.confirmarHallazgo(this,supervisor,identidad));
    }
    public void confirmarPerdida(String id, boolean supervisor, boolean concluida) {
        procesar(id,"confirmarPerdida()",supervisor+":"+concluida,()->estado.confirmarPerdida(this,supervisor,concluida));
    }
    public void confirmarRecepcionRecuperado(String id, boolean supervisor, boolean identidad, boolean recepcion, String hub) {
        procesar(id,"confirmarRecepcionRecuperado()",supervisor+":"+identidad+":"+recepcion+":"+hub,()->estado.confirmarRecepcionRecuperado(this,supervisor,identidad,recepcion,hub));
    }
    private synchronized void procesar(String id, String evento, String contenido, Runnable accion) {
        if(id==null||id.trim().isEmpty()) throw estado.guardaFalsa(evento,"eventId no vacío");
        String solicitud=evento+"|"+contenido;
        Resultado previo=resultadoPorEventId.get(id);
        if(previo!=null) {
            if(!previo.solicitud.equals(solicitud)) throw estado.guardaFalsa(evento,"eventId no reutilizado para otra petición");
            if(previo.rechazo!=null) throw previo.rechazo;
            return;
        }
        EstadoPaquete anterior=estado;int intentosPrevios=intentosEntrega;boolean cerradoPrevio=cicloCerrado;
        try {
            if(cicloCerrado) throw new TransicionInvalidaException("Final",evento,"ciclo terminado");
            accion.run();resultadoPorEventId.put(id,new Resultado(solicitud,null));
        } catch(TransicionInvalidaException e) {
            estado=anterior;intentosEntrega=intentosPrevios;cicloCerrado=cerradoPrevio;
            resultadoPorEventId.put(id,new Resultado(solicitud,e));throw e;
        }
    }
    private void autorizar(boolean actor,String evento) { if(!actor) throw estado.guardaFalsa(evento,"actorAutorizado"); }
    void cambiarEstado(EstadoPaquete nuevo) { estado=nuevo;nuevo.alEntrar(this); }
    void incrementarIntentosEntrega() { intentosEntrega++; }
    void cerrarCiclo() { cicloCerrado=true; }
    public int getIntentosEntrega() { return intentosEntrega; }
    public String getEstado() { return cicloCerrado?"Final":estado.nombre(); }
    public String getCodigoRastreo() { return codigoRastreo; }
}
