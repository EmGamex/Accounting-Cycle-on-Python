"""Capa de presentación y menú interactivo por consola para el Libro Mayor y T-Gráficas."""
from typing import Any, Callable, NamedTuple, Optional

from config import MENSAJE_ALERTA_OPCION, OPCION_SALIR
from diario.engine import GestorLibroDiario
from reportes.libro_mayor import exportar_reporte_libro_mayor
from reportes.t_graficas import exportar_reporte_t_graficas
from ui import (
    BADGE_CUADRADO,
    BADGE_DESCUADRADO,
    console,
    formatear_moneda,
    generar_tabla_mayor_formal,
    generar_tabla_sumas_y_saldos,
    generar_tabla_t_grafica,
    imprimir_alerta,
    imprimir_aviso,
    imprimir_banner,
    imprimir_coincidencias_cuentas,
    imprimir_exito,
    imprimir_menu_opciones,
)
from .engine import GestorLibroMayor, mayorizar_libro_diario
from .exceptions import MayorError


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
    badge = BADGE_CUADRADO if (mayor.cuadra or num_ctas == 0) else BADGE_DESCUADRADO
    debe_fmt = formatear_moneda(mayor.total_debe)
    haber_fmt = formatear_moneda(mayor.total_haber)
    console.print(
        f"\n[bold]Libro Mayor Actual:[/bold] [cyan]{num_ctas}[/cyan] cuenta(s) activa(s) | "
        f"Debe: [green]{debe_fmt}[/green] | Haber: [green]{haber_fmt}[/green] "
        f"{badge}"
    )


def _ver_todas_t_graficas(gestor_mayor: GestorLibroMayor) -> None:
    """Muestra todas las T-gráficas generadas en consola usando tablas Rich."""
    mayor = gestor_mayor.sincronizar()
    imprimir_banner("LIBRO MAYOR - REPORTE DE T-GRÁFICAS", border_style="cyan")
    if not mayor.cuentas:
        imprimir_aviso("No hay movimientos registrados en el Libro Mayor.")
        return
    for c in mayor.cuentas_ordenadas:
        tabla = generar_tabla_t_grafica(c)
        console.print(tabla)
        console.print("")
    tabla_resumen = generar_tabla_sumas_y_saldos(mayor)
    console.print(tabla_resumen)


def _consultar_t_grafica_individual(gestor_mayor: GestorLibroMayor) -> None:
    """Solicita código o nombre de cuenta y muestra su T-gráfica estilizada con Rich."""
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
        imprimir_coincidencias_cuentas(coincidencias, limite=len(coincidencias))
        sel = input("Seleccione el número de cuenta: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(coincidencias):
            cuenta = coincidencias[int(sel) - 1]
        else:
            imprimir_alerta("Selección cancelada.")
            return

    console.print("")
    console.print(generar_tabla_t_grafica(cuenta))


def _ver_mayor_formal(gestor_mayor: GestorLibroMayor) -> None:
    """Muestra el reporte del Libro Mayor formal a 3 columnas en consola usando tablas Rich."""
    mayor = gestor_mayor.sincronizar()
    imprimir_banner("LIBRO MAYOR DE OPERACIONES (A 3 COLUMNAS)", border_style="cyan")
    if not mayor.cuentas:
        imprimir_aviso("No hay movimientos registrados en el Libro Mayor.")
        return
    for folio, c in enumerate(mayor.cuentas_ordenadas, start=1):
        tabla = generar_tabla_mayor_formal(c, folio=folio)
        console.print(tabla)
        console.print("")
    tabla_resumen = generar_tabla_sumas_y_saldos(mayor)
    console.print(tabla_resumen)


def _ver_resumen_sumas_y_saldos(gestor_mayor: GestorLibroMayor) -> None:
    """Imprime una tabla compacta con las sumas y saldos de cada cuenta."""
    mayor = gestor_mayor.sincronizar()
    tabla = generar_tabla_sumas_y_saldos(mayor)
    console.print(tabla)

    badge = BADGE_CUADRADO if mayor.cuadra else BADGE_DESCUADRADO
    console.print(f"Estado: {badge}")


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


def _mostrar_menu(acciones: list[AccionMenu]) -> None:
    """Imprime las opciones disponibles del menú basándose en su posición."""
    console.print("\nOperaciones de Libro Mayor disponibles:")
    opciones = [(str(idx), item.descripcion) for idx, item in enumerate(acciones, start=1)]
    imprimir_menu_opciones(opciones, texto_salir="Volver al menú principal", salir_codigo=OPCION_SALIR)


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
        _mostrar_menu(acciones)

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
