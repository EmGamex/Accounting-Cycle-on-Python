"""Capa de presentación y menú interactivo por consola para el Libro Mayor y T-Gráficas."""
from typing import Any, Callable, NamedTuple, Optional

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
from .engine import GestorLibroMayor, mayorizar_libro_diario
from .exceptions import MayorError

ANCHO_BANNER = 70
OPCION_SALIR = "0"
MENSAJE_ALERTA_OPCION = "  (!) Opción no reconocida. Intente nuevamente."


class AccionMenu(NamedTuple):
    """Estructura para representar una opción ejecutable en el menú interactivo."""
    descripcion: str
    accion: Callable[[GestorLibroMayor], Any]


def _imprimir_encabezado() -> None:
    """Imprime el banner del menú del Libro Mayor."""
    separador = "=" * ANCHO_BANNER
    print(separador)
    print("       SISTEMA DE LIBRO MAYOR Y T-GRÁFICAS (GUATEMALA)")
    print(separador)


def _imprimir_resumen_mayor(gestor_mayor: GestorLibroMayor) -> None:
    """Muestra un resumen conciso del estado actual del mayor."""
    mayor = gestor_mayor.sincronizar()
    num_ctas = len(mayor.cuentas)
    estado = "CUADRADO" if mayor.cuadra or num_ctas == 0 else "DESCUADRADO"
    print(
        f"\nLibro Mayor Actual: {num_ctas} cuenta(s) activa(s) | "
        f"Debe: Q{mayor.total_debe:,.2f} | Haber: Q{mayor.total_haber:,.2f} [{estado}]"
    )


def _ver_todas_t_graficas(gestor_mayor: GestorLibroMayor) -> None:
    """Muestra todas las T-gráficas generadas en consola."""
    mayor = gestor_mayor.sincronizar()
    print("\n" + generar_texto_todas_t_graficas(mayor))


def _consultar_t_grafica_individual(gestor_mayor: GestorLibroMayor) -> None:
    """Solicita código o nombre de cuenta y muestra su T-gráfica."""
    mayor = gestor_mayor.sincronizar()
    if not mayor.cuentas:
        print("\n  (!) El Libro Mayor no tiene cuentas registradas.")
        return

    termino = input("\nIngrese código o nombre de la cuenta a consultar: ").strip()
    if not termino:
        return

    coincidencias = mayor.buscar_cuentas(termino)
    if not coincidencias:
        print(f"  (!) No se encontró ninguna cuenta que coincida con '{termino}'.")
        return

    if len(coincidencias) == 1:
        cuenta = coincidencias[0]
    else:
        print(f"\nSe encontraron {len(coincidencias)} cuentas:")
        for idx, c in enumerate(coincidencias, start=1):
            print(f"  [{idx}] [{c.codigo}] {c.nombre}")
        sel = input("Seleccione el número de cuenta: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(coincidencias):
            cuenta = coincidencias[int(sel) - 1]
        else:
            print("  (!) Selección cancelada.")
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
    mayor = gestor_mayor.sincronizar()
    cuentas = mayor.cuentas_ordenadas
    ancho = 80
    print("\n" + linea_doble(ancho))
    print("RESUMEN DE CUENTAS MAYORIZADAS (SUMAS Y SALDOS)".center(ancho))
    print(linea_doble(ancho))
    print(f"{'CODIGO':<8} {'CUENTA':<28} {'DEBE':>12} {'HABER':>12} {'S.DEUDOR':>12} {'S.ACREEDOR':>12}")
    print(linea_simple(ancho))

    for c in cuentas:
        d_str = formato_moneda(c.total_debe)
        h_str = formato_moneda(c.total_haber)
        sd_str = formato_moneda(c.saldo_deudor) if c.saldo_deudor > 0 else "-"
        sa_str = formato_moneda(c.saldo_acreedor) if c.saldo_acreedor > 0 else "-"
        nom_trunc = c.nombre[:26] + ".." if len(c.nombre) > 28 else c.nombre
        print(f"{c.codigo:<8} {nom_trunc:<28} {d_str:>12} {h_str:>12} {sd_str:>12} {sa_str:>12}")

    print(linea_simple(ancho))
    tot_d = formato_moneda(mayor.total_debe)
    tot_h = formato_moneda(mayor.total_haber)
    tot_sd = formato_moneda(mayor.total_saldos_deudores)
    tot_sa = formato_moneda(mayor.total_saldos_acreedores)
    print(f"{'SUMAS:':<37} {tot_d:>12} {tot_h:>12} {tot_sd:>12} {tot_sa:>12}")
    print(linea_doble(ancho))
    print(f"Estado: {'CUADRE EXACTO' if mayor.cuadra else 'DESCUADRADO'}")


def _exportar_t_graficas_txt(gestor_mayor: GestorLibroMayor) -> None:
    """Exporta las T-Gráficas a un archivo de texto en disco."""
    ruta = input("Ruta o nombre del archivo [t_graficas_mayor.txt]: ").strip() or "t_graficas_mayor.txt"
    try:
        mayor = gestor_mayor.sincronizar()
        ruta_gen = exportar_reporte_t_graficas(mayor, ruta_archivo=ruta)
        print(f"  [OK] Reporte de T-Gráficas exportado exitosamente a '{ruta_gen}'.")
    except Exception as e:
        print(f"  (!) Error al exportar: {e}")


def _exportar_mayor_formal_txt(gestor_mayor: GestorLibroMayor) -> None:
    """Exporta el Libro Mayor formal a un archivo de texto en disco."""
    ruta = input("Ruta o nombre del archivo [libro_mayor_formal.txt]: ").strip() or "libro_mayor_formal.txt"
    try:
        mayor = gestor_mayor.sincronizar()
        ruta_gen = exportar_reporte_libro_mayor(mayor, ruta_archivo=ruta)
        print(f"  [OK] Reporte de Libro Mayor formal exportado exitosamente a '{ruta_gen}'.")
    except Exception as e:
        print(f"  (!) Error al exportar: {e}")


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
        print("\nOperaciones de Libro Mayor disponibles:")
        for idx, item in enumerate(acciones, start=1):
            print(f"  [{idx}] {item.descripcion}")
        print(f"  [{OPCION_SALIR}] Volver al menú principal")

        prompt_rango = f"[1-{len(acciones)}, {OPCION_SALIR}]"
        seleccion = input(f"\nSeleccione una opción {prompt_rango}: ").strip()

        if seleccion == OPCION_SALIR:
            print("\nRetornando al menú principal...")
            break

        if seleccion.isdigit() and 1 <= int(seleccion) <= len(acciones):
            try:
                acciones[int(seleccion) - 1].accion(gestor_mayor)
            except KeyboardInterrupt:
                print("\n  [!] Operación cancelada por el usuario.")
            except Exception as e:
                print(f"\n  (!) Error durante la operación: {e}")
        else:
            print(MENSAJE_ALERTA_OPCION)
