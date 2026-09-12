"""Capa de presentación y menú interactivo por consola para el Libro Diario."""
from typing import Any, Callable, NamedTuple, Optional

from diario.asistentes import (
    registrar_compra_asistida,
    registrar_operacion_simple_asistida,
    registrar_partida_libre_asistida,
    registrar_venta_asistida,
)
from diario.engine import GestorLibroDiario
from reportes import generar_texto_libro_diario

# Constantes de formato y presentación
ANCHO_BANNER = 70
OPCION_SALIR = "0"
MENSAJE_ALERTA_OPCION = "  (!) Opción no reconocida. Intente nuevamente."


class AccionMenu(NamedTuple):
    """Estructura para representar una opción ejecutable en el menú interactivo."""
    descripcion: str
    accion: Callable[[GestorLibroDiario], Any]


def _imprimir_encabezado() -> None:
    """Imprime el banner principal del sistema."""
    separador = "=" * ANCHO_BANNER
    print(separador)
    print("         SISTEMA DE LIBRO DIARIO CONTABLE (GUATEMALA)")
    print(separador)


def _imprimir_resumen_libro(gestor: GestorLibroDiario) -> None:
    """Muestra el estado actual del libro diario."""
    total_partidas = len(gestor.libro.partidas)
    print(
        f"\nLibro Diario Actual: {total_partidas} partida(s) registradas "
        f"| Siguiente: Partida #{gestor.siguiente_numero}"
    )


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
            lambda g: print("\n" + generar_texto_libro_diario(g.libro)),
        ),
    ]


def _mostrar_menu(acciones: list[AccionMenu]) -> None:
    """Imprime las opciones disponibles del menú basándose en su posición."""
    print("Operaciones diarias disponibles:")
    for idx, item in enumerate(acciones, start=1):
        print(f"  [{idx}] {item.descripcion}")
    print(f"  [{OPCION_SALIR}] Volver / Salir")


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
            print("\n¡Gracias por utilizar el Sistema de Libro Diario!")
            break

        if seleccion.isdigit() and 1 <= int(seleccion) <= len(acciones):
            acciones[int(seleccion) - 1].accion(gestor)
        else:
            print(MENSAJE_ALERTA_OPCION)
