"""Capa de presentación y menú interactivo por consola para el Balance de 4 Columnas y Cierre."""
from typing import Any, Callable, NamedTuple, Optional

from config import (
    ARCHIVO_BALANCE_4C_DEFAULT,
    ARCHIVO_BALANCE_GENERAL_DEFAULT,
    MENSAJE_ALERTA_OPCION,
    OPCION_SALIR,
)
from diario.engine import GestorLibroDiario
from mayor.engine import GestorLibroMayor
from reportes.balance import exportar_reporte_balance_cierre
from reportes.balance_comprobacion import exportar_reporte_balance_4_columnas
from ui import (
    BADGE_CUADRADO,
    BADGE_DESCUADRADO,
    console,
    formatear_moneda,
    generar_tabla_balance_4_columnas,
    generar_tabla_balance_general,
    generar_tabla_estado_resultados,
    imprimir_alerta,
    imprimir_aviso,
    imprimir_banner,
    imprimir_exito,
    imprimir_menu_opciones,
)

from .engine import GestorBalance


class AccionMenu(NamedTuple):
    """Estructura para representar una opción ejecutable en el menú de Balances."""
    descripcion: str
    accion: Callable[[GestorBalance], Any]


def _imprimir_encabezado() -> None:
    """Imprime el banner del módulo de Balances."""
    imprimir_banner("SISTEMA DE BALANCES: 4 COLUMNAS Y SITUACIÓN GENERAL", border_style="cyan")


def _imprimir_resumen_balance(gestor_balance: GestorBalance) -> None:
    """Muestra un resumen conciso del estado de cuadre del Balance de 4 Columnas."""
    b4 = gestor_balance.obtener_balance_4_columnas(sincronizar=True)
    num_filas = len(b4.filas)
    badge = BADGE_CUADRADO if (b4.cuadra or num_filas == 0) else BADGE_DESCUADRADO
    d_fmt = formatear_moneda(b4.total_debe)
    h_fmt = formatear_moneda(b4.total_haber)
    sd_fmt = formatear_moneda(b4.total_saldos_deudores)
    sa_fmt = formatear_moneda(b4.total_saldos_acreedores)

    console.print(
        f"\n[bold]Balance de 4 Columnas:[/bold] [cyan]{num_filas}[/cyan] cuenta(s) | "
        f"Sumas: [green]{d_fmt}[/green] / [green]{h_fmt}[/green] | "
        f"Saldos: [green]{sd_fmt}[/green] / [green]{sa_fmt}[/green] "
        f"{badge}"
    )


def _ver_balance_4_columnas(gestor_balance: GestorBalance) -> None:
    """Muestra la matriz completa del Balance de 4 Columnas estilizada con Rich."""
    b4 = gestor_balance.obtener_balance_4_columnas(sincronizar=True)
    imprimir_banner("BALANCE DE COMPROBACIÓN Y SALDOS (4 COLUMNAS)", border_style="cyan")
    if not b4.filas:
        imprimir_aviso("No hay movimientos registrados para generar el Balance de 4 Columnas.")
        return
    tabla = generar_tabla_balance_4_columnas(b4)
    console.print(tabla)


def _ver_balance_general(gestor_balance: GestorBalance) -> None:
    """Muestra el Balance de Situación General de Cierre clasificado."""
    bg = gestor_balance.obtener_balance_general(sincronizar=True)
    imprimir_banner("BALANCE DE SITUACIÓN GENERAL DE CIERRE", border_style="cyan")
    if not bg.estructura:
        imprimir_aviso("No hay cuentas reales registradas para generar el Balance General.")
        return
    tabla = generar_tabla_balance_general(bg)
    console.print(tabla)


def _ver_estado_resultados(gestor_balance: GestorBalance) -> None:
    """Muestra el Estado de Resultados condensado."""
    bg = gestor_balance.obtener_balance_general(sincronizar=True)
    imprimir_banner("ESTADO DE RESULTADOS (PÉRDIDAS Y GANANCIAS)", border_style="cyan")
    if not bg.resumen_resultados:
        imprimir_aviso("No hay cuentas de resultados registradas en el ejercicio.")
        return
    tabla = generar_tabla_estado_resultados(bg.resumen_resultados)
    console.print(tabla)


def _exportar_balance_4c_txt(gestor_balance: GestorBalance) -> None:
    """Exporta el Balance de 4 Columnas a un archivo de texto plano."""
    ruta = input(f"Ruta o nombre del archivo [{ARCHIVO_BALANCE_4C_DEFAULT}]: ").strip() or ARCHIVO_BALANCE_4C_DEFAULT
    try:
        b4 = gestor_balance.obtener_balance_4_columnas(sincronizar=True)
        ruta_gen = exportar_reporte_balance_4_columnas(b4, ruta_archivo=ruta)
        imprimir_exito(f"Balance de 4 Columnas exportado exitosamente a '{ruta_gen}'.")
    except Exception as e:
        imprimir_alerta(f"Error al exportar balance: {e}")


def _exportar_balance_general_txt(gestor_balance: GestorBalance) -> None:
    """Exporta el Balance de Situación General de Cierre a un archivo de texto plano."""
    ruta = input(f"Ruta o nombre del archivo [{ARCHIVO_BALANCE_GENERAL_DEFAULT}]: ").strip() or ARCHIVO_BALANCE_GENERAL_DEFAULT
    try:
        bg = gestor_balance.obtener_balance_general(sincronizar=True)
        ruta_gen = exportar_reporte_balance_cierre(bg, ruta_archivo=ruta)
        imprimir_exito(f"Balance de Situación General exportado exitosamente a '{ruta_gen}'.")
    except Exception as e:
        imprimir_alerta(f"Error al exportar balance general: {e}")


def _obtener_acciones_balance() -> list[AccionMenu]:
    """Retorna las acciones disponibles para el submenú de Balances."""
    return [
        AccionMenu("Ver Balance de Comprobación y Saldos (4 Columnas)", _ver_balance_4_columnas),
        AccionMenu("Ver Balance de Situación General de Cierre", _ver_balance_general),
        AccionMenu("Ver Estado de Resultados (Ingresos vs Gastos / Ganancia)", _ver_estado_resultados),
        AccionMenu("Exportar Balance de 4 Columnas a archivo (.txt)", _exportar_balance_4c_txt),
        AccionMenu("Exportar Balance de Situación General a archivo (.txt)", _exportar_balance_general_txt),
    ]


def _mostrar_menu(acciones: list[AccionMenu]) -> None:
    """Imprime el menú de opciones del balance."""
    console.print("\nOperaciones de Balances disponibles:")
    opciones = [(str(idx), item.descripcion) for idx, item in enumerate(acciones, start=1)]
    imprimir_menu_opciones(opciones, texto_salir="Volver al menú principal", salir_codigo=OPCION_SALIR)


def iniciar_flujo_balance(
    gestor_balance: Optional[GestorBalance] = None,
    gestor_diario: Optional[GestorLibroDiario] = None,
    gestor_mayor: Optional[GestorLibroMayor] = None,
) -> None:
    """Punto de entrada interactivo para el módulo de Balance de Comprobación y Cierre."""
    if gestor_balance is None:
        gestor_balance = GestorBalance(gestor_diario=gestor_diario, gestor_mayor=gestor_mayor)

    _imprimir_encabezado()
    acciones = _obtener_acciones_balance()

    while True:
        _imprimir_resumen_balance(gestor_balance)
        _mostrar_menu(acciones)

        prompt_rango = f"[1-{len(acciones)}, {OPCION_SALIR}]"
        seleccion = input(f"\nSeleccione una opción {prompt_rango}: ").strip()

        if seleccion == OPCION_SALIR:
            console.print("\nRetornando al menú principal...")
            break

        if seleccion.isdigit() and 1 <= int(seleccion) <= len(acciones):
            try:
                acciones[int(seleccion) - 1].accion(gestor_balance)
            except KeyboardInterrupt:
                imprimir_aviso("Operación cancelada por el usuario.")
            except Exception as e:
                imprimir_alerta(f"Error durante la operación: {e}")
        else:
            imprimir_alerta(MENSAJE_ALERTA_OPCION)
