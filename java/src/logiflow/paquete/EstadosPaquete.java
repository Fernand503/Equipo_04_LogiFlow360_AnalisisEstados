package logiflow.paquete;

/*
 * Estados concretos de SMD_PaqueteFisico (15 estados, incluido Bajo_Custodia).
 * El estado compuesto Bajo_Custodia se traduce a una clase abstracta: las transiciones
 * dibujadas desde su borde (reportarSiniestro, reportarExtravio) se heredan en sus 7 subestados.
 * La guarda [actorAutorizado] de los pasos logísticos la valida PaqueteFisico.autorizar()
 * antes de delegar; aquí solo aparecen las guardas propias de cada transición.
 */

// ------------------------------------------------------------------ fuera del compuesto
final class ManifiestoCreado implements EstadoPaquete {
    public String nombre() { return "Manifiesto_Creado"; }
    // escanearRecepcion() [etiquetaValida] / registrarCustodiaOrigen()
    @Override public void escanearRecepcion(PaqueteFisico p, boolean etiquetaValida) {
        if (!etiquetaValida) throw guardaFalsa("escanearRecepcion()", "[etiquetaValida]");
        p.cambiarEstado(new RecibidoEnHubOrigen());
    }
}

// ------------------------------------------------------------------ compuesto Bajo_Custodia
abstract class BajoCustodia implements EstadoPaquete {
    // Bajo_Custodia --reportarSiniestro() [reporteVerificado] / abrirInvestigacion()--> Siniestrado_En_Investigacion
    @Override public void reportarSiniestro(PaqueteFisico p, boolean reporteVerificado) {
        if (!reporteVerificado) throw guardaFalsa("reportarSiniestro()", "[reporteVerificado]");
        p.cambiarEstado(new SiniestradoEnInvestigacion());
    }
    // Bajo_Custodia --reportarExtravio() [reporteVerificado] / iniciarBusqueda()--> Extraviado
    @Override public void reportarExtravio(PaqueteFisico p, boolean reporteVerificado) {
        if (!reporteVerificado) throw guardaFalsa("reportarExtravio()", "[reporteVerificado]");
        p.cambiarEstado(new Extraviado());
    }
}

final class RecibidoEnHubOrigen extends BajoCustodia {
    public String nombre() { return "Recibido_En_Hub_Origen"; }
    @Override public void iniciarClasificacion(PaqueteFisico p) { p.cambiarEstado(new EnClasificacion()); }
    // confirmarEntrega() NO se sobrescribe: desde aquí entregar es imposible (Pregunta 2).
}

final class EnClasificacion extends BajoCustodia {
    public String nombre() { return "En_Clasificacion"; }
    @Override public void confirmarSalidaHub(PaqueteFisico p) { p.cambiarEstado(new EnTransitoInterHub()); }
}

final class EnTransitoInterHub extends BajoCustodia {
    public String nombre() { return "En_Transito_Inter_Hub"; }
    @Override public void escanearLlegadaDestino(PaqueteFisico p) { p.cambiarEstado(new EnHubDestino()); }
}

final class EnHubDestino extends BajoCustodia {
    public String nombre() { return "En_Hub_Destino"; }
    @Override public void asignarRuta(PaqueteFisico p) { p.cambiarEstado(new AsignadoARutaUltimaMilla()); }
}

final class AsignadoARutaUltimaMilla extends BajoCustodia {
    public String nombre() { return "Asignado_A_Ruta_Ultima_Milla"; }
    @Override public void confirmarSalidaRuta(PaqueteFisico p) { p.cambiarEstado(new EnCaminoAEntrega()); }
}

final class EnCaminoAEntrega extends BajoCustodia {
    public String nombre() { return "En_Camino_A_Entrega"; }

    // confirmarEntrega() [actorAutorizado && evidenciaValida] / guardarPruebaEntrega()
    @Override public void confirmarEntrega(PaqueteFisico p, boolean evidenciaValida) {
        if (!evidenciaValida) throw guardaFalsa("confirmarEntrega()", "[evidenciaValida]");
        p.cambiarEstado(new EntregadoExitosamente());
    }

    // reportarAusencia() [intentosEntrega < 3] / incrementarIntentosEntrega()
    @Override public void reportarAusencia(PaqueteFisico p) {
        if (!(p.getIntentosEntrega() < 3)) throw guardaFalsa("reportarAusencia()", "[intentosEntrega < 3]");
        p.incrementarIntentosEntrega();
        p.cambiarEstado(new EntregaFallidaAusente());
    }
}

final class EntregaFallidaAusente extends BajoCustodia {
    public String nombre() { return "Entrega_Fallida_Ausente"; }

    // Transiciones de finalización, guardas complementarias:
    //   [intentosEntrega < 3]  / programarNuevaVisita() --> Asignado_A_Ruta_Ultima_Milla
    //   [intentosEntrega >= 3] / ordenarRetorno()       --> Retornado_A_Centro_Distribucion
    @Override public void alEntrar(PaqueteFisico p) {
        if (p.getIntentosEntrega() < 3) {
            p.cambiarEstado(new AsignadoARutaUltimaMilla());
        } else {
            p.cambiarEstado(new RetornadoACentroDistribucion());
        }
    }
}

// ------------------------------------------------------------------ fuera del compuesto
/** Fin legítimo: en el diagrama sale hacia el Final State. No acepta eventos. */
final class EntregadoExitosamente implements EstadoPaquete {
    public String nombre() { return "Entregado_Exitosamente"; }
    @Override public void alEntrar(PaqueteFisico p) { p.cerrarCiclo(); }
}

final class RetornadoACentroDistribucion implements EstadoPaquete {
    public String nombre() { return "Retornado_A_Centro_Distribucion"; }
    // confirmarRetorno() [recepcionHubConfirmada] / cerrarCicloDeReparto() --> Final
    @Override public void confirmarRetorno(PaqueteFisico p, boolean recepcionHubConfirmada) {
        if (!recepcionHubConfirmada) throw guardaFalsa("confirmarRetorno()", "[recepcionHubConfirmada]");
        p.cerrarCiclo();
    }
}

final class SiniestradoEnInvestigacion implements EstadoPaquete {
    public String nombre() { return "Siniestrado_En_Investigacion"; }
    @Override public void cerrarInvestigacion(PaqueteFisico p, boolean supervisor, boolean recuperable) {
        if(!supervisor) throw guardaFalsa("cerrarInvestigacion()","supervisorAutorizado");
        p.cambiarEstado(recuperable?new RecuperadoPendienteRecepcion():new PerdidaConfirmada());
    }
}

final class Extraviado implements EstadoPaquete {
    public String nombre() { return "Extraviado"; }
    @Override public void confirmarHallazgo(PaqueteFisico p, boolean supervisor, boolean identidad) {
        if(!(supervisor&&identidad)) throw guardaFalsa("confirmarHallazgo()","supervisorAutorizado && identidadConfirmada");
        p.cambiarEstado(new RecuperadoPendienteRecepcion());
    }
    @Override public void confirmarPerdida(PaqueteFisico p, boolean supervisor, boolean concluida) {
        if(!(supervisor&&concluida)) throw guardaFalsa("confirmarPerdida()","supervisorAutorizado && investigacionConcluida");
        p.cambiarEstado(new PerdidaConfirmada());
    }
}
final class RecuperadoPendienteRecepcion implements EstadoPaquete {
    public String nombre() { return "Recuperado_Pendiente_Recepcion"; }
    @Override public void confirmarRecepcionRecuperado(PaqueteFisico p, boolean supervisor, boolean identidad, boolean recepcion, String hub) {
        if(!(supervisor&&identidad&&recepcion&&("ORIGEN".equals(hub)||"DESTINO".equals(hub))))
            throw guardaFalsa("confirmarRecepcionRecuperado()","supervisor, identidad, recepción y hub válidos");
        p.cambiarEstado("ORIGEN".equals(hub)?new RecibidoEnHubOrigen():new EnHubDestino());
    }
}
final class PerdidaConfirmada implements EstadoPaquete {
    public String nombre() { return "Perdida_Confirmada"; }
    @Override public void alEntrar(PaqueteFisico p) { p.cerrarCiclo(); }
}
