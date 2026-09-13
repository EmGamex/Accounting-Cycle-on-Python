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
from config import MENSAJE_ALERTA_OPCION, OPCION_SALIR
from reportes import imprimir_partida_rich
from ui import (
    COLOR_AVISO,
    COLOR_EXITO,
    COLOR_SECUNDARIO,
    console,
    formatear_moneda,
    imprimir_alerta,
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
    from rich.table import Table
    from ui.temas import BORDE_TABLA, COLOR_TEXTO
    from config import FORMATO_FECHA

    tabla = Table(title=f"{titulo} ({len(gestor.libro.partidas)} partidas)", box=BORDE_TABLA)
    tabla.add_column("No.", justify="right", style="bold cyan", no_wrap=True)
    tabla.add_column("Fecha", style="dim", no_wrap=True)
    tabla.add_column("Glosa / Descripción", style=COLOR_TEXTO)
    tabla.add_column("Origen", style="dim cyan", no_wrap=True)
    tabla.add_column("Total Debe (Q)", justify="right", style="green", no_wrap=True)
    tabla.add_column("Total Haber (Q)", justify="right", style="green", no_wrap=True)
    tabla.add_column("Estado", justify="center", no_wrap=True)

    for p in gestor.libro.partidas:
        fecha_str = p.fecha.strftime(FORMATO_FECHA) if hasattr(p.fecha, "strftime") else str(p.fecha)
        glosa_corta = (p.glosa[:40] + "..") if len(p.glosa) > 42 else p.glosa
        origen_str = p.origen.value if hasattr(p.origen, "value") else str(p.origen)
        estado = "[green]✓ Cuadra[/green]" if p.cuadra else "[red]✗ Descuadrada[/red]"

        tabla.add_row(
            str(p.numero),
            fecha_str,
            glosa_corta,
            origen_str,
            formatear_moneda(p.total_debe),
            formatear_moneda(p.total_haber),
            estado,
        )

    console.print(tabla)


def _consultar_partida_por_numero(gestor: GestorLibroDiario) -> None:
    """Solicita un número correlativo y despliega su partida mostrando previamente el listado."""
    if not gestor.libro.partidas:
        imprimir_alerta("El Libro Diario no contiene partidas asentadas.")
        return

    _mostrar_resumen_partidas_tabla(gestor, "CONSULTA DE PARTIDAS")
    num_str = input(f"\nNúmero de partida a consultar [1-{gestor.libro.partidas[-1].numero}, Enter para cancelar]: ").strip()
    if not num_str:
        return
    if not num_str.isdigit():
        imprimir_alerta("Debe ingresar un número válido.")
        return
    partida = gestor.obtener_partida(int(num_str))
    if not partida:
        imprimir_alerta(f"No existe la Partida No. {num_str}.")
        return
    imprimir_partida_rich(partida)


def _modificar_partida_existente(gestor: GestorLibroDiario) -> None:
    """Permite modificar la glosa, fecha o redefinir líneas de una partida existente."""
    from diario.prompts import buscar_o_seleccionar_cuenta, pedir_fecha, pedir_monto
    from diario.models import MovimientoLinea, PartidaDiario

    if not gestor.libro.partidas:
        imprimir_alerta("El Libro Diario no contiene partidas asentadas.")
        return

    _mostrar_resumen_partidas_tabla(gestor, "MODIFICAR PARTIDA")
    num_str = input(f"\nNúmero de partida a modificar [1-{gestor.libro.partidas[-1].numero}, Enter para cancelar]: ").strip()
    if not num_str:
        return
    if not num_str.isdigit():
        imprimir_alerta("Debe ingresar un número válido.")
        return
    numero = int(num_str)
    partida = gestor.obtener_partida(numero)
    if not partida:
        imprimir_alerta(f"No existe la Partida No. {numero}.")
        return

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
                f"  Estado -> Debe: [green]Q {nueva.total_debe:,.2f}[/green] | "
                f"Haber: [green]Q {nueva.total_haber:,.2f}[/green] | Diferencia: [yellow]Q {nueva.diferencia:,.2f}[/yellow]"
            )
            col = input("  ¿Imputar al Debe [D] o al Haber [H]? (o 'fin' para concluir): ").strip().upper()
            if col == "FIN":
                break
            if col not in ("D", "H"):
                imprimir_alerta("Opción no válida. Ingrese D para Debe o H para Haber.")
                continue

            cod, nom = buscar_o_seleccionar_cuenta("  Código o nombre de cuenta", gestor=gestor)
            monto = pedir_monto(f"  Monto a registrar en el {'DEBE' if col == 'D' else 'HABER'}: Q ")

            if col == "D":
                nueva.agregar_cargo(cod, nom, monto)
            else:
                nueva.agregar_abono(cod, nom, monto)

        if not nueva.lineas:
            imprimir_alerta("No se ingresaron líneas. Se canceló la modificación.")
            return

        if not nueva.cuadra:
            imprimir_alerta(
                f"La partida no cuadra (Diferencia: Q {nueva.diferencia:,.2f}). "
                "No se aplicaron los cambios para preservar la integridad contable."
            )
            return

        gestor.actualizar_partida(numero, nueva)
        imprimir_exito(f"Partida No. {numero} modificada y actualizada exitosamente.")
        imprimir_partida_rich(nueva)


def _eliminar_partida_existente(gestor: GestorLibroDiario) -> None:
    """Permite eliminar un asiento contable y re-correlaciona automáticamente."""
    if not gestor.libro.partidas:
        imprimir_alerta("El Libro Diario no contiene partidas asentadas.")
        return

    _mostrar_resumen_partidas_tabla(gestor, "ELIMINAR / ANULAR PARTIDA")
    num_str = input(f"\nNúmero de partida a eliminar [1-{gestor.libro.partidas[-1].numero}, Enter para cancelar]: ").strip()
    if not num_str:
        return
    if not num_str.isdigit():
        imprimir_alerta("Debe ingresar un número válido.")
        return
    numero = int(num_str)
    partida = gestor.obtener_partida(numero)
    if not partida:
        imprimir_alerta(f"No existe la Partida No. {numero}.")
        return

    imprimir_partida_rich(partida)
    confirmacion = pedir_confirmacion(
        f"¿Estás seguro de eliminar la Partida No. {numero}? Se re-correlacionarán las siguientes (s/n): ",
        default=False,
    )
    if confirmacion:
        gestor.eliminar_partida(numero, recorrelacionar=True)
        imprimir_exito(f"Partida No. {numero} eliminada. Correlativos re-indexados correctamente.")


def _obtener_acciones_diario() -> list[AccionMenu]:
    """Define la lista ordenada de operaciones disponibles en el menú."""
    return [
        AccionMenu(
            "Registrar Compra / Gasto con IVA (Crédito Fiscal 12%)",
            registrar_compra_asistida,
        ),
        AccionMenu(
            "Registrar Venta con IVA (Débito Fiscal 12%)",
            registrar_venta_asistida,
        ),
        AccionMenu(
            "Registrar Operación Simple (Traslado, Cobro a Clientes, Pago a Proveedores)",
            registrar_operacion_simple_asistida,
        ),
        AccionMenu(
            "Registrar Partida Libre / Asiento General (Línea por línea)",
            registrar_partida_libre_asistida,
        ),
        AccionMenu(
            "Regularizar IVA del Período (Ajuste Débito vs. Crédito Fiscal)",
            regularizar_iva_asistido,
        ),
        AccionMenu(
            "Consultar Partida por Número",
            _consultar_partida_por_numero,
        ),
        AccionMenu(
            "Modificar Partida Existente (Glosa, Fecha o Líneas)",
            _modificar_partida_existente,
        ),
        AccionMenu(
            "Eliminar / Anular Partida (Con Re-correlación)",
            _eliminar_partida_existente,
        ),
        AccionMenu(
            "Ver Libro Diario Completo",
            _mostrar_libro_diario,
        ),
    ]


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


def _mostrar_menu(acciones: list[AccionMenu]) -> None:
    """Imprime las opciones disponibles del menú basándose en su posición."""
    console.print("Operaciones diarias disponibles:")
    opciones = [(str(idx), item.descripcion) for idx, item in enumerate(acciones, start=1)]
    imprimir_menu_opciones(opciones, texto_salir="Volver / Salir", salir_codigo=OPCION_SALIR)


def iniciar_flujo_diario(gestor: Optional[GestorLibroDiario] = None) -> None:
    """Punto de entrada interactivo para el registro de operaciones y reportes del Libro Diario."""
    if gestor is None:
        gestor = GestorLibroDiario(estricto_cronologico=False)

    _imprimir_encabezado()
    acciones = _obtener_acciones_diario()

    while True:
        _imprimir_resumen_libro(gestor)
        _mostrar_menu(acciones)

        prompt_rango = f"[1-{len(acciones)}, {OPCION_SALIR}]"
        seleccion = input(f"\nSeleccione una opción {prompt_rango}: ").strip()

        if seleccion == OPCION_SALIR:
            _verificar_regularizacion_al_finalizar(gestor)
            console.print(f"\n[{COLOR_EXITO}]¡Gracias por utilizar el Sistema de Libro Diario![/{COLOR_EXITO}]")
            break

        if seleccion.isdigit() and 1 <= int(seleccion) <= len(acciones):
            acciones[int(seleccion) - 1].accion(gestor)
        else:
            imprimir_alerta(MENSAJE_ALERTA_OPCION)
