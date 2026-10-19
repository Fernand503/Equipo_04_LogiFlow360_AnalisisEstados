package logiflow.paquete;

public class PruebasPatronState {

    private static int total = 0;

    // Cuenta la prueba y detiene todo si falla
    private static void comprobar(boolean ok) {
        total++;
        if (!ok) throw new AssertionError("Fallo la comprobacion " + total);
    }

    // Devuelve true si la accion lanza TransicionInvalidaException
    private static boolean rechazado(Runnable accion) {
        try {
            accion.run();
            return false;
        } catch (TransicionInvalidaException e) {
            return true;
        }
    }

    // Paquete ya recibido en el hub de origen
    private static PaqueteFisico enOrigen() {
        PaqueteFisico p = new PaqueteFisico("PF");
        p.escanearRecepcion("r", true);
        return p;
    }

    // Paquete que ya salio a reparto (En_Camino_A_Entrega)
    private static PaqueteFisico enReparto() {
        PaqueteFisico p = enOrigen();
        p.iniciarClasificacion("c", true);
        p.confirmarSalidaHub("s", true);
        p.escanearLlegadaDestino("d", true);
        p.asignarRuta("a", true);
        p.confirmarSalidaRuta("v", true);
        return p;
    }

    public static void main(String[] args) {
        pruebaOrigenYFraude();
        pruebaEntrega();
        pruebaTresAusencias();
        pruebaSiniestroYExtravio();
        System.out.println(total + " comprobaciones aprobadas");
    }

    // Caso 1: el paquete nace bien y no se puede entregar desde el hub de origen
    private static void pruebaOrigenYFraude() {
        PaqueteFisico p = new PaqueteFisico("PF");
        comprobar(p.getEstado().equals("Manifiesto_Creado"));
        comprobar(rechazado(() -> p.escanearRecepcion("bad", false)));   // etiqueta invalida

        p.escanearRecepcion("r", true);
        comprobar(p.getEstado().equals("Recibido_En_Hub_Origen"));

        comprobar(rechazado(() -> p.confirmarEntrega("fraude", true, true)));   // Pregunta 2
        comprobar(p.getEstado().equals("Recibido_En_Hub_Origen"));            // el estado no cambia
        comprobar(rechazado(() -> p.confirmarEntrega("fraude", true, true)));   // mismo eventId repetido
        comprobar(rechazado(() -> p.confirmarEntrega("r", true, true)));        // eventId reutilizado
        comprobar(rechazado(() -> p.iniciarClasificacion("no", false)));        // actor no autorizado

        p.iniciarClasificacion("c", true);
        p.iniciarClasificacion("c", true);                                      // duplicado: no se aplica dos veces
        comprobar(p.getEstado().equals("En_Clasificacion"));
    }

    // Caso 2: la entrega exige evidencia y despues el ciclo termina
    private static void pruebaEntrega() {
        PaqueteFisico a = enReparto();
        comprobar(rechazado(() -> a.confirmarEntrega("sinEvidencia", true, false)));
        comprobar(a.getEstado().equals("En_Camino_A_Entrega"));

        a.confirmarEntrega("entrega", true, true);
        comprobar(a.getEstado().equals("Final"));
        comprobar(rechazado(() -> a.reportarExtravio("tarde", true)));          // nada sale del Final
    }

    // Caso 3: dos ausencias reprograman, la tercera ordena el retorno
    private static void pruebaTresAusencias() {
        PaqueteFisico b = enReparto();
        b.reportarAusencia("uno");
        b.reportarAusencia("uno");                                              // duplicado
        comprobar(b.getIntentosEntrega() == 1);
        comprobar(b.getEstado().equals("Asignado_A_Ruta_Ultima_Milla"));

        b.confirmarSalidaRuta("dosSalida", true);
        b.reportarAusencia("dos");
        b.confirmarSalidaRuta("tresSalida", true);
        b.reportarAusencia("tres");
        comprobar(b.getIntentosEntrega() == 3 && b.getEstado().equals("Retornado_A_Centro_Distribucion"));
        comprobar(rechazado(() -> b.confirmarSalidaRuta("cuarta", true)));      // no hay cuarta visita

        comprobar(rechazado(() -> b.confirmarRetorno("sinRecepcion", false)));
        b.confirmarRetorno("retorno", true);
        comprobar(b.getEstado().equals("Final"));
    }

    // Caso 4: siniestro y extravio, con recuperacion o perdida
    private static void pruebaSiniestroYExtravio() {
        PaqueteFisico c = enOrigen();
        c.reportarSiniestro("siniestro", true);
        comprobar(c.getEstado().equals("Siniestrado_En_Investigacion"));
        c.cerrarInvestigacion("recuperable", true, true);
        comprobar(c.getEstado().equals("Recuperado_Pendiente_Recepcion"));
        comprobar(rechazado(() -> c.confirmarRecepcionRecuperado("virtual", true, true, false, "ORIGEN")));  // sin recepcion fisica
        comprobar(rechazado(() -> c.confirmarRecepcionRecuperado("otro", true, true, true, "OTRO")));       // hub invalido
        c.confirmarRecepcionRecuperado("escaneo", true, true, true, "ORIGEN");
        comprobar(c.getEstado().equals("Recibido_En_Hub_Origen"));

        PaqueteFisico d = enOrigen();
        d.reportarExtravio("perdido", true);
        d.confirmarHallazgo("hallado", true, true);
        d.confirmarRecepcionRecuperado("destino", true, true, true, "DESTINO");
        comprobar(d.getEstado().equals("En_Hub_Destino"));

        PaqueteFisico e = enOrigen();
        e.reportarExtravio("perdido", true);
        comprobar(rechazado(() -> e.confirmarPerdida("inconcluso", true, false)));
        e.confirmarPerdida("concluido", true, true);
        comprobar(e.getEstado().equals("Final"));

        PaqueteFisico f = enOrigen();
        f.reportarSiniestro("danado", true);
        f.cerrarInvestigacion("irrecuperable", true, false);
        comprobar(f.getEstado().equals("Final"));
    }
}