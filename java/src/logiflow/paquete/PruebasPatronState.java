package logiflow.paquete;

/** Pruebas de comportamiento; ejecutar sin dependencias externas. */
public class PruebasPatronState {
    private static int n;
    private static void comprobar(boolean ok) { n++;if(!ok) throw new AssertionError("Falló comprobación "+n); }
    private static boolean rechazado(Runnable r) { try{r.run();return false;}catch(TransicionInvalidaException e){return true;} }
    private static PaqueteFisico origen() { PaqueteFisico p=new PaqueteFisico("PF");p.escanearRecepcion("r",true);return p; }
    private static PaqueteFisico reparto() {
        PaqueteFisico p=origen();p.iniciarClasificacion("c",true);p.confirmarSalidaHub("s",true);p.escanearLlegadaDestino("d",true);p.asignarRuta("a",true);p.confirmarSalidaRuta("v",true);return p;
    }
    public static void main(String[] args) {
        PaqueteFisico p=new PaqueteFisico("PF");
        comprobar(p.getEstado().equals("Manifiesto_Creado"));
        comprobar(rechazado(()->p.escanearRecepcion("bad",false)));
        p.escanearRecepcion("r",true);comprobar(p.getEstado().equals("Recibido_En_Hub_Origen"));
        comprobar(rechazado(()->p.confirmarEntrega("fraude",true,true)));
        comprobar(p.getEstado().equals("Recibido_En_Hub_Origen"));
        comprobar(rechazado(()->p.confirmarEntrega("fraude",true,true)));
        comprobar(rechazado(()->p.confirmarEntrega("r",true,true)));
        comprobar(rechazado(()->p.iniciarClasificacion("no",false)));
        p.iniciarClasificacion("c",true);p.iniciarClasificacion("c",true);comprobar(p.getEstado().equals("En_Clasificacion"));
        PaqueteFisico a=reparto();
        comprobar(rechazado(()->a.confirmarEntrega("sinEvidencia",true,false)));
        comprobar(a.getEstado().equals("En_Camino_A_Entrega"));
        a.confirmarEntrega("entrega",true,true);comprobar(a.getEstado().equals("Final"));
        comprobar(rechazado(()->a.reportarExtravio("tarde",true)));
        PaqueteFisico b=reparto();b.reportarAusencia("uno");b.reportarAusencia("uno");
        comprobar(b.getIntentosEntrega()==1);comprobar(b.getEstado().equals("Asignado_A_Ruta_Ultima_Milla"));
        b.confirmarSalidaRuta("dosSalida",true);b.reportarAusencia("dos");b.confirmarSalidaRuta("tresSalida",true);b.reportarAusencia("tres");
        comprobar(b.getIntentosEntrega()==3&&b.getEstado().equals("Retornado_A_Centro_Distribucion"));
        comprobar(rechazado(()->b.confirmarSalidaRuta("cuarta",true)));
        comprobar(rechazado(()->b.confirmarRetorno("sinRecepcion",false)));
        b.confirmarRetorno("retorno",true);comprobar(b.getEstado().equals("Final"));
        PaqueteFisico c=origen();c.reportarSiniestro("siniestro",true);comprobar(c.getEstado().equals("Siniestrado_En_Investigacion"));
        c.cerrarInvestigacion("recuperable",true,true);comprobar(c.getEstado().equals("Recuperado_Pendiente_Recepcion"));
        comprobar(rechazado(()->c.confirmarRecepcionRecuperado("virtual",true,true,false,"ORIGEN")));
        comprobar(rechazado(()->c.confirmarRecepcionRecuperado("otro",true,true,true,"OTRO")));
        c.confirmarRecepcionRecuperado("escaneo",true,true,true,"ORIGEN");comprobar(c.getEstado().equals("Recibido_En_Hub_Origen"));
        PaqueteFisico d=origen();d.reportarExtravio("perdido",true);d.confirmarHallazgo("hallado",true,true);d.confirmarRecepcionRecuperado("destino",true,true,true,"DESTINO");comprobar(d.getEstado().equals("En_Hub_Destino"));
        PaqueteFisico e=origen();e.reportarExtravio("perdido",true);comprobar(rechazado(()->e.confirmarPerdida("inconcluso",true,false)));
        e.confirmarPerdida("concluido",true,true);comprobar(e.getEstado().equals("Final"));
        PaqueteFisico f=origen();f.reportarSiniestro("danado",true);f.cerrarInvestigacion("irrecuperable",true,false);comprobar(f.getEstado().equals("Final"));
        System.out.println(n+" comprobaciones aprobadas");
    }
}
