"""Capa de presentación y menú interactivo por consola para el Libro Diario."""
from typing import Any, Callable, NamedTuple, Optional

from diario.asistentes import (
    registrar_compra_asistida,
    registrar_operacion_simple_asistida,
    registrar_partida_libre_asistida,
    registrar_venta_asistida,
    regularizar_iva_asistido,
)
from diario.engine import GestorLibroDiario
from diario.operaciones import NOMBRE_IVA_CREDITO, NOMBRE_IVA_DEBITO
from config import MENSAJE_ALERTA_OPCION, OPCION_SALIR, SIMBOLO_MONEDA
from reportes import imprimir_partida_rich
from ui import (
    COLOR_AVISO,
    COLOR_EXITO,
    COLOR_SECUNDARIO,
    console,
    formatear_moneda,
    generar_tabla_resumen_partidas,
    imprimir_alerta,
    imprimir_aviso,
    imprimir_banner,
    imprimir_exito,
    imprimir_menu_opciones,
    pedir_confirmacion,
)


class AccionMenu(NamedTuple):
    """Estructura para representar una opción ejecutable en el menú interactivo."""
    descripcion: str
    accion: Callable[[GestorLibroDiario], Any]


def _imprimir_encabezado() -> None:
    """Imprime el banner principal del sistema."""
    imprimir_banner("SISTEMA DE LIBRO DIARIO CONTABLE (GUATEMALA)", border_style=COLOR_SECUNDARIO)


def _imprimir_resumen_libro(gestor: GestorLibroDiario) -> None:
    """Muestra el estado actual del libro diario."""
    total_partidas = len(gestor.libro.partidas)
    console.print(
        f"\n[bold]Libro Diario Actual:[/bold] [{COLOR_SECUNDARIO}]{total_partidas}[/{COLOR_SECUNDARIO}] partida(s) registradas "
        f"| [bold]Siguiente:[/bold] [{COLOR_EXITO}]Partida #{gestor.siguiente_numero}[/{COLOR_EXITO}]"
    )


def _mostrar_libro_diario(gestor: GestorLibroDiario) -> None:
    """Muestra todas las partidas asentadas en el diario con tablas Rich."""
    if not gestor.libro.partidas:
        imprimir_alerta("El Libro Diario no contiene partidas asentadas.")
        return
    for partida in gestor.libro.partidas:
        imprimir_partida_rich(partida)


def _mostrar_resumen_partidas_tabla(gestor: GestorLibroDiario, titulo: str = "PARTIDAS REGISTRADAS EN EL LIBRO DIARIO") -> None:
    """Muestra una tabla compacta con todas las partidas del diario y sus datos clave."""
    tabla = generar_tabla_resumen_partidas(gestor.libro.partidas, titulo=titulo)
    console.print(tabla)


def _seleccionar_partida_interactiva(gestor: GestorLibroDiario, accion_nombre: str) -> Optional[Any]:
    """Muestra el resumen de partidas y solicita de forma estandarizada seleccionar una partida."""
    if not gestor.libro.partidas:
        imprimir_alerta("El Libro Diario no contiene partidas asentadas.")
        return None

    _mostrar_resumen_partidas_tabla(gestor, f"{accion_nombre.upper()} PARTIDA")
    max_num = gestor.libro.partidas[-1].numero
    num_str = input(f"\nNúmero de partida a {accion_nombre.lower()} [1-{max_num}, Enter para cancelar]: ").strip()
    if not num_str:
        return None
    if not num_str.isdigit():
        imprimir_alerta("Debe ingresar un número válido.")
        return None
    numero = int(num_str)
    partida = gestor.obtener_partida(numero)
    if not partida:
        imprimir_alerta(f"No existe la Partida No. {numero}.")
        return None
    return partida


def _consultar_partida_por_numero(gestor: GestorLibroDiario) -> None:
    """Solicita un número correlativo y despliega su partida mostrando previamente el listado."""
    partida = _seleccionar_partida_interactiva(gestor, "consultar")
    if partida:
        imprimir_partida_rich(partida)


def _modificar_partida_existente(gestor: GestorLibroDiario) -> None:
    """Permite modificar la glosa, fecha o redefinir líneas de una partida existente."""
    from diario.prompts import buscar_o_seleccionar_cuenta, pedir_fecha, pedir_monto
    from diario.models import MovimientoLinea, PartidaDiario

    partida = _seleccionar_partida_interactiva(gestor, "modificar")
    if not partida:
        return
    numero = partida.numero

    console.print(f"\n[bold]Partida actual No. {numero}:[/bold]")
    imprimir_partida_rich(partida)

    console.print("\n¿Qué deseas modificar?")
    console.print("  [1] Solo la glosa / explicación")
    console.print("  [2] Solo la fecha")
    console.print("  [3] Redefinir las líneas contables (Debe / Haber)")
    console.print("  [4] Modificación completa (Fecha, Glosa y Líneas)")
    console.print("  [0] Cancelar")
    op = input("Seleccione opción [1-4, 0]: ").strip()

    if op == "0" or not op:
        return

    if op == "1":
        nueva_glosa = input(f"Nueva glosa [{partida.glosa}]: ").strip() or partida.glosa
        partida.glosa = nueva_glosa
        imprimir_exito(f"Glosa de la Partida No. {numero} actualizada exitosamente.")
        imprimir_partida_rich(partida)
        return

    if op == "2":
        nueva_fecha = pedir_fecha(f"Nueva fecha [{partida.fecha.isoformat()}]: ")
        partida.fecha = nueva_fecha
        imprimir_exito(f"Fecha de la Partida No. {numero} actualizada exitosamente.")
        imprimir_partida_rich(partida)
        return

    if op in ("3", "4"):
        fecha = pedir_fecha(f"Fecha de la partida [{partida.fecha.isoformat()}]: ") if op == "4" else partida.fecha
        glosa = (input(f"Glosa [{partida.glosa}]: ").strip() or partida.glosa) if op == "4" else partida.glosa
        doc = partida.documento_soporte

        nueva = PartidaDiario(
            numero=numero,
            fecha=fecha,
            glosa=glosa,
            origen=partida.origen,
            documento_soporte=doc,
        )

        console.print("\n[bold]INGRESO DE NUEVAS LÍNEAS (Escriba 'fin' en el código para terminar)[/bold]")
        while True:
            console.print(
                f"  Estado -> Debe: [{COLOR_EXITO}]{formatear_moneda(nueva.total_debe)}[/{COLOR_EXITO}] | "
                f"Haber: [{COLOR_EXITO}]{formatear_moneda(nueva.total_haber)}[/{COLOR_EXITO}] | "
                f"Diferencia: [{COLOR_AVISO}]{formatear_moneda(nueva.diferencia)}[/{COLOR_AVISO}]"
            )
            col = input("  ¿Imputar al Debe [D] o al Haber [H]? (o 'fin' para concluir): ").strip().upper()
            if col == "FIN":
                break
            if col not in ("D", "H"):
                imprimir_alerta("Opción no válida. Ingrese D para Debe o H para Haber.")
                continue

            cod, nom = buscar_o_seleccionar_cuenta("  Código o nombre de cuenta", gestor=gestor)
            monto = pedir_monto(f"  Monto a registrar en el {'DEBE' if col == 'D' else 'HABER'} ({SIMBOLO_MONEDA}): ")

            if col == "D":
                nueva.agregar_cargo(cod, nom, monto)
            else:
                nueva.agregar_abono(cod, nom, monto)

        if not nueva.lineas:
            imprimir_alerta("No se ingresaron líneas. Se canceló la modificación.")
            return

        if not nueva.cuadra:
            imprimir_alerta(
                f"La partida no cuadra (Diferencia: {formatear_moneda(nueva.diferencia)}). "
                "No se aplicaron los cambios para preservar la integridad contable."
            )
            return

        gestor.actualizar_partida(numero, nueva)
        imprimir_exito(f"Partida No. {numero} modificada y actualizada exitosamente.")
        imprimir_partida_rich(nueva)


def _eliminar_partida_existente(gestor: GestorLibroDiario) -> None:
    """Permite eliminar un asiento contable y re-correlaciona automáticamente."""
    partida = _seleccionar_partida_interactiva(gestor, "eliminar")
    if not partida:
        return
    numero = partida.numero

    imprimir_partida_rich(partida)
    confirmacion = pedir_confirmacion(
        f"¿Estás seguro de eliminar la Partida No. {numero}? Se re-correlacionarán las siguientes (s/n): ",
        default=False,
    )
    if confirmacion:
        gestor.eliminar_partida(numero, recorrelacionar=True)
        imprimir_exito(f"Partida No. {numero} eliminada. Correlativos re-indexados correctamente.")


def _mover_partida_posicion(gestor: GestorLibroDiario) -> None:
    """Permite mover una partida contable a una nueva posición correlativa."""
    partida = _seleccionar_partida_interactiva(gestor, "mover")
    if not partida:
        return

    origen = partida.numero
    total = len(gestor.libro.partidas)
    destino_str = input(f"Nueva posición para la Partida No. {origen} [1-{total}, Enter para cancelar]: ").strip()
    if not destino_str:
        return
    if not destino_str.isdigit():
        imprimir_alerta("Debe ingresar un número de posición válido.")
        return

    destino = int(destino_str)
    if not (1 <= destino <= total):
        imprimir_alerta(f"La posición debe estar entre 1 y {total}.")
        return

    if origen == destino:
        imprimir_aviso(f"La partida ya se encuentra en la posición No. {destino}.")
        return

    gestor.mover_partida(origen, destino)
    imprimir_exito(f"Partida movida exitosamente de la posición #{origen} a la #{destino}.")
    _mostrar_resumen_partidas_tabla(gestor, "LIBRO DIARIO ACTUALIZADO")


def _ordenar_cronologicamente_interactivo(gestor: GestorLibroDiario) -> None:
    """Reordena todas las partidas por fecha ascendente y re-indexa los correlativos."""
    if not gestor.libro.partidas:
        imprimir_alerta("El Libro Diario no contiene partidas asentadas.")
        return

    if len(gestor.libro.partidas) == 1:
        imprimir_aviso("Solo hay 1 partida en el libro diario. No es necesario reordenar.")
        return

    confirmado = pedir_confirmacion(
        "¿Deseas reordenar todas las partidas por fecha cronológica ascendente? (s/n): ",
        default=False,
    )
    if confirmado:
        gestor.ordenar_partidas_cronologicamente()
        imprimir_exito("Partidas reordenadas cronológicamente y correlativos re-indexados.")
        _mostrar_resumen_partidas_tabla(gestor, "LIBRO DIARIO REORDENADO")


def _ejecutar_submenu(titulo_menu: str, acciones: list[AccionMenu], gestor: GestorLibroDiario) -> None:
    """Controlador genérico para la navegación y ejecución de submenús interactivos."""
    while True:
        console.print(f"\n[bold]{titulo_menu}:[/bold]")
        opciones = [(str(idx), item.descripcion) for idx, item in enumerate(acciones, start=1)]
        imprimir_menu_opciones(opciones, texto_salir="Volver al Menú Principal", salir_codigo=OPCION_SALIR)

        seleccion = input(f"\nSeleccione una opción [1-{len(acciones)}, {OPCION_SALIR}]: ").strip()
        if seleccion == OPCION_SALIR:
            break

        if seleccion.isdigit() and 1 <= int(seleccion) <= len(acciones):
            acciones[int(seleccion) - 1].accion(gestor)
        else:
            imprimir_alerta(MENSAJE_ALERTA_OPCION)


def _submenu_registro_operaciones(gestor: GestorLibroDiario) -> None:
    """Submenú especializado en el asiento de transacciones comerciales y operativas."""
    acciones = [
        AccionMenu("Registrar Compra / Gasto con IVA (Crédito Fiscal 12%)", registrar_compra_asistida),
        AccionMenu("Registrar Venta con IVA (Débito Fiscal 12%)", registrar_venta_asistida),
        AccionMenu("Registrar Operación Simple (Cobro a Clientes, Pago a Proveedores, Depósitos)", registrar_operacion_simple_asistida),
        AccionMenu("Registrar Partida Libre / Asiento General (Línea por línea)", registrar_partida_libre_asistida),
    ]
    _ejecutar_submenu("REGISTRO DE OPERACIONES DIARIAS", acciones, gestor)


def _submenu_gestion_partidas(gestor: GestorLibroDiario) -> None:
    """Submenú especializado en la consulta, modificación, reordenamiento y anulación de partidas."""
    acciones = [
        AccionMenu("Consultar Partida por Número", _consultar_partida_por_numero),
        AccionMenu("Modificar Partida Existente (Glosa, Fecha o Líneas)", _modificar_partida_existente),
        AccionMenu("Reordenar / Mover Partida de Posición", _mover_partida_posicion),
        AccionMenu("Reordenar Todo el Libro por Fecha Cronológica", _ordenar_cronologicamente_interactivo),
        AccionMenu("Eliminar / Anular Partida (Con Re-correlación)", _eliminar_partida_existente),
    ]
    _ejecutar_submenu("GESTIÓN Y REORGANIZACIÓN DE PARTIDAS", acciones, gestor)


def _submenu_reportes_diario(gestor: GestorLibroDiario) -> None:
    """Submenú para visualizar partidas asentadas en detalle o resumen."""
    acciones = [
        AccionMenu("Ver Libro Diario Completo (Detallado en Tablas)", _mostrar_libro_diario),
        AccionMenu("Ver Resumen General de Partidas (Tabla compacta)", lambda g: _mostrar_resumen_partidas_tabla(g)),
    ]
    _ejecutar_submenu("CONSULTAS Y REPORTES DEL LIBRO DIARIO", acciones, gestor)


def _verificar_regularizacion_al_finalizar(gestor: GestorLibroDiario) -> None:
    """Detecta si hay saldos pendientes de compensar en IVA y ofrece regularizarlos antes de salir."""
    if gestor.puede_regularizar_iva():
        credito, debito = gestor.obtener_saldos_iva()
        console.print(
            f"\n[{COLOR_AVISO}]¡Aviso de Cierre de Período![/{COLOR_AVISO}] Se detectaron saldos pendientes en "
            f"{NOMBRE_IVA_CREDITO} ({formatear_moneda(credito)}) y {NOMBRE_IVA_DEBITO} ({formatear_moneda(debito)})."
        )
        if pedir_confirmacion("¿Deseas regularizar el IVA antes de finalizar el Libro Diario?", default=True):
            regularizar_iva_asistido(gestor)


def _obtener_menus_principales() -> list[AccionMenu]:
    """Define los módulos o áreas principales del Libro Diario."""
    return [
        AccionMenu("Registro de Operaciones (Compras, Ventas, Tesorería, Asiento Libre)", _submenu_registro_operaciones),
        AccionMenu("Gestión de Partidas (Consultar, Modificar, Reordenar, Eliminar)", _submenu_gestion_partidas),
        AccionMenu("Consultas y Reportes (Ver Libro Diario Completo, Resumen)", _submenu_reportes_diario),
        AccionMenu("Procesos Fiscales y Cierre (Regularización de IVA)", regularizar_iva_asistido),
    ]


def iniciar_flujo_diario(gestor: Optional[GestorLibroDiario] = None) -> None:
    """Punto de entrada interactivo para el registro de operaciones y reportes del Libro Diario."""
    if gestor is None:
        gestor = GestorLibroDiario(estricto_cronologico=False)

    _imprimir_encabezado()
    menus = _obtener_menus_principales()

    while True:
        _imprimir_resumen_libro(gestor)
        console.print("Áreas de trabajo disponibles:")
        opciones = [(str(idx), item.descripcion) for idx, item in enumerate(menus, start=1)]
        imprimir_menu_opciones(opciones, texto_salir="Volver / Salir", salir_codigo=OPCION_SALIR)

        prompt_rango = f"[1-{len(menus)}, {OPCION_SALIR}]"
        seleccion = input(f"\nSeleccione una opción {prompt_rango}: ").strip()

        if seleccion == OPCION_SALIR:
            _verificar_regularizacion_al_finalizar(gestor)
            console.print(f"\n[{COLOR_EXITO}]¡Gracias por utilizar el Sistema de Libro Diario![/{COLOR_EXITO}]")
            break

        if seleccion.isdigit() and 1 <= int(seleccion) <= len(menus):
            menus[int(seleccion) - 1].accion(gestor)
        else:
            imprimir_alerta(MENSAJE_ALERTA_OPCION)
