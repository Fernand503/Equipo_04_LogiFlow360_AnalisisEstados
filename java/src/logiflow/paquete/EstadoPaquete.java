package logiflow.paquete;

/**
 * Interfaz Estado del patrón State para SMD_PaqueteFisico.
 * Cada evento del diagrama es un método. Por defecto TODOS se rechazan:
 * un estado concreto solo sobrescribe los eventos que tiene en su fila de la matriz.
 */
public interface EstadoPaquete {

    String nombre();

    /** Transiciones de finalización (sin trigger): se evalúan al entrar al estado. */
    default void alEntrar(PaqueteFisico p) { }

    default void escanearRecepcion(PaqueteFisico p, boolean etiquetaValida) { throw rechazo("escanearRecepcion()"); }
    default void iniciarClasificacion(PaqueteFisico p)  { throw rechazo("iniciarClasificacion()"); }
    default void confirmarSalidaHub(PaqueteFisico p)    { throw rechazo("confirmarSalidaHub()"); }
    default void escanearLlegadaDestino(PaqueteFisico p){ throw rechazo("escanearLlegadaDestino()"); }
    default void asignarRuta(PaqueteFisico p)           { throw rechazo("asignarRuta()"); }
    default void confirmarSalidaRuta(PaqueteFisico p)   { throw rechazo("confirmarSalidaRuta()"); }
    default void confirmarEntrega(PaqueteFisico p, boolean evidenciaValida) { throw rechazo("confirmarEntrega()"); }
    default void reportarAusencia(PaqueteFisico p)      { throw rechazo("reportarAusencia()"); }
    default void confirmarRetorno(PaqueteFisico p, boolean recepcionHubConfirmada) { throw rechazo("confirmarRetorno()"); }
    default void reportarSiniestro(PaqueteFisico p, boolean reporteVerificado) { throw rechazo("reportarSiniestro()"); }
    default void reportarExtravio(PaqueteFisico p, boolean reporteVerificado)  { throw rechazo("reportarExtravio()"); }
    default void cerrarInvestigacion(PaqueteFisico p, boolean supervisor, boolean recuperable) { throw rechazo("cerrarInvestigacion()"); }
    default void confirmarHallazgo(PaqueteFisico p, boolean supervisor, boolean identidad) { throw rechazo("confirmarHallazgo()"); }
    default void confirmarPerdida(PaqueteFisico p, boolean supervisor, boolean concluida) { throw rechazo("confirmarPerdida()"); }
    default void confirmarRecepcionRecuperado(PaqueteFisico p, boolean supervisor, boolean identidad, boolean recepcion, String hub) { throw rechazo("confirmarRecepcionRecuperado()"); }

    default TransicionInvalidaException rechazo(String evento) {
        return new TransicionInvalidaException(nombre(), evento, "la matriz no tiene fila para este par estado-evento");
    }

    default TransicionInvalidaException guardaFalsa(String evento, String guarda) {
        return new TransicionInvalidaException(nombre(), evento, "guarda " + guarda + " = false");
    }
}
