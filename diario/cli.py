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
OPCION_PRIMERA = "1"
OPCION_ULTIMA = "5"
MENSAJE_ALERTA_OPCION = "  (!) Opción no reconocida. Intente nuevamente."


class OpcionMenu(NamedTuple):
    """Estructura de datos para representar una opción en el menú interactivo."""
    codigo: str
    descripcion: str
    accion: Optional[Callable[[GestorLibroDiario], Any]] = None


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


def _obtener_catalogo_opciones() -> dict[str, OpcionMenu]:
    """Define las opciones disponibles en el menú interactivo."""
    opciones = [
        OpcionMenu(
            "1",
            "Registrar Compra / Gasto con IVA (Crédito Fiscal 12%)",
            registrar_compra_asistida,
        ),
        OpcionMenu(
            "2",
            "Registrar Venta con IVA (Débito Fiscal 12%)",
            registrar_venta_asistida,
        ),
        OpcionMenu(
            "3",
            "Registrar Operación Simple (Traslado, Cobro a Clientes, Pago a Proveedores)",
            registrar_operacion_simple_asistida,
        ),
        OpcionMenu(
            "4",
            "Registrar Partida Libre / Asiento General (Línea por línea)",
            registrar_partida_libre_asistida,
        ),
        OpcionMenu(
            "5",
            "Ver Libro Diario Completo",
            lambda g: print("\n" + generar_texto_libro_diario(g.libro)),
        ),
        OpcionMenu(
            OPCION_SALIR,
            "Volver / Salir",
            None,
        ),
    ]
    return {op.codigo: op for op in opciones}


def _mostrar_menu(opciones: dict[str, OpcionMenu]) -> None:
    """Imprime las opciones disponibles del menú en consola."""
    print("Operaciones diarias disponibles:")
    for op in opciones.values():
        print(f"  [{op.codigo}] {op.descripcion}")


def iniciar_flujo_diario(gestor: Optional[GestorLibroDiario] = None) -> None:
    """Punto de entrada interactivo para el registro de operaciones y reportes del Libro Diario."""
    if gestor is None:
        gestor = GestorLibroDiario(estricto_cronologico=False)

    _imprimir_encabezado()
    opciones = _obtener_catalogo_opciones()

    while True:
        _imprimir_resumen_libro(gestor)
        _mostrar_menu(opciones)

        prompt_rango = f"[{OPCION_PRIMERA}-{OPCION_ULTIMA}, {OPCION_SALIR}]"
        seleccion = input(f"\nSeleccione una opción {prompt_rango}: ").strip()

        if seleccion == OPCION_SALIR:
            print("\n¡Gracias por utilizar el Sistema de Libro Diario!")
            break

        opcion = opciones.get(seleccion)
        if opcion and opcion.accion:
            opcion.accion(gestor)
        else:
            print(MENSAJE_ALERTA_OPCION)
