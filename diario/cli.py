"""Capa de presentación y menú interactivo por consola para el Libro Diario."""
from typing import Any, Callable, NamedTuple, Optional

from diario.asistentes import (
    registrar_compra_asistida,
    registrar_operacion_simple_asistida,
    registrar_partida_libre_asistida,
    registrar_venta_asistida,
)
from diario.engine import GestorLibroDiario
from config import MENSAJE_ALERTA_OPCION, OPCION_SALIR
from reportes import imprimir_partida_rich
from ui import (
    COLOR_EXITO,
    COLOR_SECUNDARIO,
    console,
    imprimir_alerta,
    imprimir_banner,
    imprimir_menu_opciones,
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
            "Ver Libro Diario Completo",
            _mostrar_libro_diario,
        ),
    ]


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
            console.print(f"\n[{COLOR_EXITO}]¡Gracias por utilizar el Sistema de Libro Diario![/{COLOR_EXITO}]")
            break

        if seleccion.isdigit() and 1 <= int(seleccion) <= len(acciones):
            acciones[int(seleccion) - 1].accion(gestor)
        else:
            imprimir_alerta(MENSAJE_ALERTA_OPCION)
