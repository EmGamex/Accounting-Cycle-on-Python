"""Capa de presentación y menú interactivo por consola para el Libro Mayor y T-Gráficas."""
from typing import Any, Callable, NamedTuple, Optional

from rich import box
from rich.table import Table

from diario.engine import GestorLibroDiario
from reportes.formato import formato_moneda, linea_doble, linea_simple
from reportes.libro_mayor import (
    exportar_reporte_libro_mayor,
    generar_texto_libro_mayor_formal,
)
from reportes.t_graficas import (
    exportar_reporte_t_graficas,
    generar_texto_t_grafica,
    generar_texto_todas_t_graficas,
)
from ui import console, imprimir_alerta, imprimir_aviso, imprimir_banner, imprimir_exito
from .engine import GestorLibroMayor, mayorizar_libro_diario
from .exceptions import MayorError

OPCION_SALIR = "0"
MENSAJE_ALERTA_OPCION = "Opción no reconocida. Intente nuevamente."


class AccionMenu(NamedTuple):
    """Estructura para representar una opción ejecutable en el menú interactivo."""
    descripcion: str
    accion: Callable[[GestorLibroMayor], Any]


def _imprimir_encabezado() -> None:
    """Imprime el banner del menú del Libro Mayor."""
    imprimir_banner("SISTEMA DE LIBRO MAYOR Y T-GRÁFICAS (GUATEMALA)", border_style="cyan")


def _imprimir_resumen_mayor(gestor_mayor: GestorLibroMayor) -> None:
    """Muestra un resumen conciso del estado actual del mayor."""
    mayor = gestor_mayor.sincronizar()
    num_ctas = len(mayor.cuentas)
    estado = "CUADRADO" if mayor.cuadra or num_ctas == 0 else "DESCUADRADO"
    color = "green" if mayor.cuadra or num_ctas == 0 else "red"
    console.print(
        f"\n[bold]Libro Mayor Actual:[/bold] [cyan]{num_ctas}[/cyan] cuenta(s) activa(s) | "
        f"Debe: [green]Q{mayor.total_debe:,.2f}[/green] | Haber: [green]Q{mayor.total_haber:,.2f}[/green] "
        f"[[bold {color}]{estado}[/bold {color}]]"
    )


def _ver_todas_t_graficas(gestor_mayor: GestorLibroMayor) -> None:
    """Muestra todas las T-gráficas generadas en consola."""
    mayor = gestor_mayor.sincronizar()
    print("\n" + generar_texto_todas_t_graficas(mayor))


def _consultar_t_grafica_individual(gestor_mayor: GestorLibroMayor) -> None:
    """Solicita código o nombre de cuenta y muestra su T-gráfica."""
    mayor = gestor_mayor.sincronizar()
    if not mayor.cuentas:
        imprimir_alerta("El Libro Mayor no tiene cuentas registradas.")
        return

    termino = input("\nIngrese código o nombre de la cuenta a consultar: ").strip()
    if not termino:
        return

    coincidencias = mayor.buscar_cuentas(termino)
    if not coincidencias:
        imprimir_alerta(f"No se encontró ninguna cuenta que coincida con '{termino}'.")
        return

    if len(coincidencias) == 1:
        cuenta = coincidencias[0]
    else:
        console.print(f"\nSe encontraron [cyan]{len(coincidencias)}[/cyan] cuentas:")
        for idx, c in enumerate(coincidencias, start=1):
            console.print(f"  [bold cyan][{idx}][/bold cyan] [{c.codigo}] {c.nombre}")
        sel = input("Seleccione el número de cuenta: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(coincidencias):
            cuenta = coincidencias[int(sel) - 1]
        else:
            imprimir_alerta("Selección cancelada.")
            return

    print("\n" + linea_simple(55))
    print(generar_texto_t_grafica(cuenta))
    print(linea_simple(55))


def _ver_mayor_formal(gestor_mayor: GestorLibroMayor) -> None:
    """Muestra el reporte del Libro Mayor a 3 columnas en consola."""
    mayor = gestor_mayor.sincronizar()
    print("\n" + generar_texto_libro_mayor_formal(mayor))


def _ver_resumen_sumas_y_saldos(gestor_mayor: GestorLibroMayor) -> None:
    """Imprime una tabla compacta con las sumas y saldos de cada cuenta."""
    from ui.tablas import generar_tabla_sumas_y_saldos

    mayor = gestor_mayor.sincronizar()
    tabla = generar_tabla_sumas_y_saldos(mayor)
    console.print(tabla)

    cuadre_msg = "CUADRE EXACTO" if mayor.cuadra else "DESCUADRADO"
    color = "green" if mayor.cuadra else "red"
    console.print(f"Estado: [[bold {color}]{cuadre_msg}[/bold {color}]]")


def _exportar_t_graficas_txt(gestor_mayor: GestorLibroMayor) -> None:
    """Exporta las T-Gráficas a un archivo de texto en disco."""
    ruta = input("Ruta o nombre del archivo [t_graficas_mayor.txt]: ").strip() or "t_graficas_mayor.txt"
    try:
        mayor = gestor_mayor.sincronizar()
        ruta_gen = exportar_reporte_t_graficas(mayor, ruta_archivo=ruta)
        imprimir_exito(f"Reporte de T-Gráficas exportado exitosamente a '{ruta_gen}'.")
    except Exception as e:
        imprimir_alerta(f"Error al exportar: {e}")


def _exportar_mayor_formal_txt(gestor_mayor: GestorLibroMayor) -> None:
    """Exporta el Libro Mayor formal a un archivo de texto en disco."""
    ruta = input("Ruta o nombre del archivo [libro_mayor_formal.txt]: ").strip() or "libro_mayor_formal.txt"
    try:
        mayor = gestor_mayor.sincronizar()
        ruta_gen = exportar_reporte_libro_mayor(mayor, ruta_archivo=ruta)
        imprimir_exito(f"Reporte de Libro Mayor formal exportado exitosamente a '{ruta_gen}'.")
    except Exception as e:
        imprimir_alerta(f"Error al exportar: {e}")


def _obtener_acciones_mayor() -> list[AccionMenu]:
    """Retorna las acciones disponibles para el submenú de Mayor."""
    return [
        AccionMenu("Ver T-Gráficas de todas las cuentas", _ver_todas_t_graficas),
        AccionMenu("Consultar T-Gráfica de una cuenta específica", _consultar_t_grafica_individual),
        AccionMenu("Ver Libro Mayor formal (A 3 columnas)", _ver_mayor_formal),
        AccionMenu("Ver Resumen de Sumas y Saldos (Pre-Balance)", _ver_resumen_sumas_y_saldos),
        AccionMenu("Exportar T-Gráficas a archivo de texto (.txt)", _exportar_t_graficas_txt),
        AccionMenu("Exportar Libro Mayor formal a archivo (.txt)", _exportar_mayor_formal_txt),
    ]


def iniciar_flujo_mayor(
    gestor_mayor: Optional[GestorLibroMayor] = None,
    gestor_diario: Optional[GestorLibroDiario] = None,
) -> None:
    """Punto de entrada interactivo para el Libro Mayor y T-Gráficas."""
    if gestor_mayor is None:
        if gestor_diario is not None:
            gestor_mayor = GestorLibroMayor(gestor_diario.libro)
        else:
            gestor_mayor = GestorLibroMayor()

    _imprimir_encabezado()
    acciones = _obtener_acciones_mayor()

    while True:
        _imprimir_resumen_mayor(gestor_mayor)
        console.print("\nOperaciones de Libro Mayor disponibles:")
        for idx, item in enumerate(acciones, start=1):
            console.print(f"  [bold cyan][{idx}][/bold cyan] {item.descripcion}")
        console.print(f"  [bold dim][{OPCION_SALIR}][/bold dim] Volver al menú principal")

        prompt_rango = f"[1-{len(acciones)}, {OPCION_SALIR}]"
        seleccion = input(f"\nSeleccione una opción {prompt_rango}: ").strip()

        if seleccion == OPCION_SALIR:
            console.print("\nRetornando al menú principal...")
            break

        if seleccion.isdigit() and 1 <= int(seleccion) <= len(acciones):
            try:
                acciones[int(seleccion) - 1].accion(gestor_mayor)
            except KeyboardInterrupt:
                imprimir_aviso("Operación cancelada por el usuario.")
            except Exception as e:
                imprimir_alerta(f"Error durante la operación: {e}")
        else:
            imprimir_alerta(MENSAJE_ALERTA_OPCION)
