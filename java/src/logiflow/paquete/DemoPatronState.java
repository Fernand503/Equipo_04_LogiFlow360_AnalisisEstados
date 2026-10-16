package logiflow.paquete;

/**
 * Demostración ilustrativa (no es una suite de pruebas del sistema):
 * transición válida, transición rechazada, evento duplicado y tercera ausencia.
 */
public class DemoPatronState {

    public static void main(String[] args) {

        System.out.println("1) Fraude (Pregunta 2): confirmarEntrega() con el paquete en Recibido_En_Hub_Origen");
        PaqueteFisico p1 = new PaqueteFisico("PF-0001");
        p1.escanearRecepcion("e-001", true);
        try {
            p1.confirmarEntrega("e-002", true, true);
        } catch (TransicionInvalidaException e) {
            System.out.println("  -> p1 sigue en " + p1.getEstado());
        }

        System.out.println("\n2) Camino válido hasta la entrega y cierre del ciclo");
        PaqueteFisico p2 = new PaqueteFisico("PF-0002");
        hastaReparto(p2, "a");
        p2.confirmarEntrega("a-07", true, true);
        System.out.println("  -> p2 en " + p2.getEstado());

        System.out.println("\n3) Evento duplicado: el mismo reportarAusencia() llega dos veces");
        PaqueteFisico p3 = new PaqueteFisico("PF-0003");
        hastaReparto(p3, "b");
        p3.reportarAusencia("b-07");
        p3.reportarAusencia("b-07");   // reintento de red con el mismo eventId
        System.out.println("  -> intentosEntrega = " + p3.getIntentosEntrega() + " (no 2)");

        System.out.println("\n4) Segunda y tercera ausencia: la tercera ordena el retorno");
        p3.confirmarSalidaRuta("b-08", true);
        p3.reportarAusencia("b-09");
        p3.confirmarSalidaRuta("b-10", true);
        p3.reportarAusencia("b-11");
        System.out.println("  -> p3 en " + p3.getEstado() + ", intentosEntrega = " + p3.getIntentosEntrega());
        try {
            p3.confirmarSalidaRuta("b-12", true);   // no existe cuarta visita
        } catch (TransicionInvalidaException e) { /* ya impreso */ }
        p3.confirmarRetorno("b-13", true);
        System.out.println("  -> p3 en " + p3.getEstado());
    }

    private static void hastaReparto(PaqueteFisico p, String x) {
        p.escanearRecepcion(x + "-01", true);
        p.iniciarClasificacion(x + "-02", true);
        p.confirmarSalidaHub(x + "-03", true);
        p.escanearLlegadaDestino(x + "-04", true);
        p.asignarRuta(x + "-05", true);
        p.confirmarSalidaRuta(x + "-06", true);
    }
}
