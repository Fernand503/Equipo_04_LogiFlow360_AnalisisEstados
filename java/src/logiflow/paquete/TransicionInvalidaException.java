package logiflow.paquete;

/** Se lanza cuando el estado actual no admite el evento recibido o su guarda es falsa. */
public class TransicionInvalidaException extends RuntimeException {

    private final String estadoActual;
    private final String evento;

    public TransicionInvalidaException(String estadoActual, String evento, String motivo) {
        super("Evento '" + evento + "' rechazado en estado '" + estadoActual + "': " + motivo);
        this.estadoActual = estadoActual;
        this.evento = evento;
    }

    public String getEstadoActual() { return estadoActual; }
    public String getEvento() { return evento; }
}
