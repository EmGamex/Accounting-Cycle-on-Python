"""Capa de presentación y menú interactivo por consola para el cálculo de nómina y planillas."""
from typing import Any, Callable, List, NamedTuple, Optional, Tuple

from .calculos import calcular_boleta
from .contabilidad import generar_partida_contable
from .io_handlers import (
    cargar_empleados_csv,
    crear_plantilla_csv_ejemplo,
    exportar_planilla_csv,
    imprimir_boleta,
    imprimir_partida,
    solicitar_datos_interactivo,
)
from .models import PartidaContable, ResultadoPlanilla


from config import (
    ARCHIVO_PLANILLA_DEFAULT,
    ARCHIVO_PLANTILLA_CSV_DEFAULT,
    MENSAJE_ALERTA_OPCION,
    OPCION_SALIR,
    RESPUESTAS_AFIRMATIVAS,
)
from ui import (
    console,
    imprimir_alerta,
    imprimir_aviso,
    imprimir_banner,
    imprimir_exito,
    imprimir_menu_opciones,
)

OPCION_PREDETERMINADA_MENU: int = 0
OPCION_SALIR_CSV_LEGACY: str = "4"


class AccionMenu(NamedTuple):
    """Estructura para representar una opción ejecutable en el menú interactivo."""
    descripcion: str
    accion: Callable[[], Any]


def flujo_interactivo(planillas_existentes: Optional[List[ResultadoPlanilla]] = None) -> List[ResultadoPlanilla]:
    """Captura secuencial de empleados desde la consola con control de duplicados."""
    planillas: List[ResultadoPlanilla] = list(planillas_existentes) if planillas_existentes else []
    while True:
        datos = solicitar_datos_interactivo()
        nombre_norm = datos.nombre.strip().lower()

        idx_existente = -1
        for idx, p in enumerate(planillas):
            if p.empleado.strip().lower() == nombre_norm:
                idx_existente = idx
                break

        if idx_existente != -1:
            confirmar = input(f"\nEl empleado '{datos.nombre}' ya existe en la nómina. ¿Deseas sobrescribir sus datos? (s/n) [s]: ").strip().lower()
            if confirmar not in RESPUESTAS_AFIRMATIVAS and confirmar != "":
                console.print("[yellow]Ingreso cancelado para este empleado.[/yellow]")
                continuar = input("\n¿Deseas ingresar otro empleado? (s/n): ").strip().lower()
                if continuar not in RESPUESTAS_AFIRMATIVAS or not continuar:
                    break
                continue

        resultado = calcular_boleta(datos)
        if idx_existente != -1:
            planillas[idx_existente] = resultado
            imprimir_exito(f"Empleado '{datos.nombre}' actualizado en la planilla.")
        else:
            planillas.append(resultado)

        imprimir_boleta(resultado)

        continuar = input("\n¿Deseas ingresar otro empleado? (s/n): ").strip().lower()
        if continuar not in RESPUESTAS_AFIRMATIVAS or not continuar:
            break
    return planillas


def _generar_plantilla_csv_accion() -> None:
    """Acción de generar plantilla CSV de ejemplo."""
    prompt = f"Nombre o ruta del archivo [{ARCHIVO_PLANTILLA_CSV_DEFAULT}]: "
    ruta = input(prompt).strip() or ARCHIVO_PLANTILLA_CSV_DEFAULT
    crear_plantilla_csv_ejemplo(ruta)
    imprimir_exito(f"Plantilla generada exitosamente en: {ruta}")


def _procesar_archivo_csv(ruta: str, planillas_actuales: List[ResultadoPlanilla]) -> List[ResultadoPlanilla]:
    """Lee y procesa empleados desde una ruta CSV dada."""
    try:
        empleados = cargar_empleados_csv(ruta)
        if not empleados:
            imprimir_alerta("No se encontraron empleados en el archivo.")
            return planillas_actuales
        nuevos_resultados = []
        for emp in empleados:
            res = calcular_boleta(emp)
            nuevos_resultados.append(res)
            imprimir_boleta(res)
        imprimir_exito(f"Se procesaron {len(nuevos_resultados)} empleado(s) desde el archivo.")
        return planillas_actuales + nuevos_resultados
    except FileNotFoundError:
        imprimir_alerta(f"El archivo '{ruta}' no fue encontrado.")
    except Exception as e:
        imprimir_alerta(f"Error al procesar el archivo CSV: {e}")
    return planillas_actuales


def _cargar_empleados_default_accion(planillas_actuales: List[ResultadoPlanilla]) -> List[ResultadoPlanilla]:
    """Acción de cargar empleados directamente desde el archivo de plantilla predeterminado."""
    return _procesar_archivo_csv(ARCHIVO_PLANTILLA_CSV_DEFAULT, planillas_actuales)


def _cargar_empleados_personalizado_accion(planillas_actuales: List[ResultadoPlanilla]) -> List[ResultadoPlanilla]:
    """Acción de solicitar una ruta de archivo CSV personalizada y cargar empleados."""
    ruta = input("Ruta del archivo CSV a cargar: ").strip()
    if not ruta:
        imprimir_alerta("Ruta vacía. Operación cancelada.")
        return planillas_actuales
    return _procesar_archivo_csv(ruta, planillas_actuales)


def _cargar_empleados_csv_accion(planillas_actuales: List[ResultadoPlanilla]) -> List[ResultadoPlanilla]:
    """Compatibilidad: delega en la carga personalizada."""
    return _cargar_empleados_personalizado_accion(planillas_actuales)


def _exportar_planillas_csv_accion(planillas_actuales: List[ResultadoPlanilla]) -> None:
    """Acción de exportar planillas existentes a archivo CSV."""
    prompt = f"Nombre de archivo de destino [{ARCHIVO_PLANILLA_DEFAULT}]: "
    ruta = input(prompt).strip() or ARCHIVO_PLANILLA_DEFAULT
    exportar_planilla_csv(planillas_actuales, ruta)
    imprimir_exito(f"Planilla exportada exitosamente en: {ruta}")


def _obtener_acciones_csv(planillas_actuales: List[ResultadoPlanilla], contenedor: list[List[ResultadoPlanilla]]) -> List[AccionMenu]:
    """Construye las acciones disponibles para el submenú CSV según su posición secuencial."""
    def ejecutar_carga_default() -> None:
        contenedor[0] = _cargar_empleados_default_accion(contenedor[0])

    def ejecutar_carga_personalizada() -> None:
        contenedor[0] = _cargar_empleados_personalizado_accion(contenedor[0])

    acciones = [
        AccionMenu(
            f"Generar archivo '{ARCHIVO_PLANTILLA_CSV_DEFAULT}' de ejemplo",
            _generar_plantilla_csv_accion,
        ),
        AccionMenu(
            f"Cargar empleados desde '{ARCHIVO_PLANTILLA_CSV_DEFAULT}'",
            ejecutar_carga_default,
        ),
        AccionMenu(
            "Cargar empleados desde una ruta personalizada",
            ejecutar_carga_personalizada,
        ),
    ]

    if planillas_actuales:
        acciones.append(
            AccionMenu(
                f"Exportar planillas actuales a '{ARCHIVO_PLANILLA_DEFAULT}'",
                lambda: _exportar_planillas_csv_accion(contenedor[0]),
            )
        )

    return acciones


def menu_herramientas_csv(planillas_actuales: List[ResultadoPlanilla]) -> List[ResultadoPlanilla]:
    """Menú secundario para carga o exportación de archivos CSV mapeado por índice."""
    imprimir_banner("HERRAMIENTAS CSV (OPCIONALES)", border_style="blue")
    contenedor = [list(planillas_actuales)]
    acciones = _obtener_acciones_csv(planillas_actuales, contenedor)

    opciones = [(str(idx), item.descripcion) for idx, item in enumerate(acciones, start=1)]
    imprimir_menu_opciones(opciones, texto_salir="Volver al menú principal", salir_codigo=OPCION_SALIR)

    prompt_rango = f"[1-{len(acciones)}, {OPCION_SALIR}]"
    opcion = input(f"\nSeleccione una opción {prompt_rango}: ").strip()

    if opcion in (OPCION_SALIR, OPCION_SALIR_CSV_LEGACY):
        return contenedor[0]

    if opcion.isdigit():
        idx = int(opcion) - 1
        if 0 <= idx < len(acciones):
            acciones[idx].accion()
            return contenedor[0]

    imprimir_alerta(MENSAJE_ALERTA_OPCION)
    return contenedor[0]


def _mostrar_resumen_boletas_accion(planillas_almacenadas: List[ResultadoPlanilla]) -> None:
    """Muestra una tabla de resumen con todos los empleados y permite ver boletas individuales."""
    if not planillas_almacenadas:
        imprimir_alerta("No hay planillas registradas.")
        return

    from rich.table import Table
    from ui.temas import BORDE_TABLA, COLOR_TEXTO
    from ui import formatear_moneda

    tabla = Table(title=f"NÓMINA DE SUELDOS ({len(planillas_almacenadas)} empleados)", box=BORDE_TABLA)
    tabla.add_column("No.", justify="right", style="dim", no_wrap=True)
    tabla.add_column("Empleado", style="bold cyan")
    tabla.add_column("Departamento", style=COLOR_TEXTO)
    tabla.add_column("Devengado (Q)", justify="right", style="green", no_wrap=True)
    tabla.add_column("IGSS Lab (Q)", justify="right", style="yellow", no_wrap=True)
    tabla.add_column("Descuentos (Q)", justify="right", style="red", no_wrap=True)
    tabla.add_column("Líquido a Recibir (Q)", justify="right", style="bold green", no_wrap=True)

    for idx, p in enumerate(planillas_almacenadas, start=1):
        tabla.add_row(
            str(idx),
            p.empleado,
            p.departamento,
            formatear_moneda(p.total_devengado),
            formatear_moneda(p.descuento_igss),
            formatear_moneda(p.total_descuentos),
            formatear_moneda(p.liquido_recibir),
        )

    console.print(tabla)

    sel = input("\nIngrese el número de empleado para ver su boleta completa (o Enter para volver): ").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(planillas_almacenadas):
        imprimir_boleta(planillas_almacenadas[int(sel) - 1])


def _modificar_o_eliminar_empleado_accion(
    planillas_almacenadas: List[ResultadoPlanilla],
) -> Optional[Any]:
    """Permite modificar o eliminar un empleado registrado en la nómina."""
    if not planillas_almacenadas:
        imprimir_alerta("No hay empleados registrados en la planilla.")
        return None

    console.print("\n[bold]Empleados actualmente registrados:[/bold]")
    for idx, p in enumerate(planillas_almacenadas, start=1):
        console.print(f"  [{idx}] {p.empleado} ({p.departamento}) - Líquido: Q {p.liquido_recibir:,.2f}")

    sel = input(f"\nSeleccione el número de empleado a gestionar [1-{len(planillas_almacenadas)}, 0 para cancelar]: ").strip()
    if not sel.isdigit() or int(sel) < 1 or int(sel) > len(planillas_almacenadas):
        return None

    idx_target = int(sel) - 1
    emp_actual = planillas_almacenadas[idx_target]

    console.print(f"\nGestión para: [bold cyan]{emp_actual.empleado}[/bold cyan]")
    console.print("  [1] Reingresar / Modificar datos del empleado")
    console.print("  [2] Eliminar empleado de la nómina")
    console.print("  [0] Cancelar")

    op = input("Seleccione opción [1-2, 0]: ").strip()
    if op == "1":
        console.print(f"\nReingrese los datos actualizados para {emp_actual.empleado}:")
        datos = solicitar_datos_interactivo()
        nuevo_res = calcular_boleta(datos)
        planillas_almacenadas[idx_target] = nuevo_res
        imprimir_exito(f"Empleado '{nuevo_res.empleado}' modificado exitosamente.")
        imprimir_boleta(nuevo_res)
    elif op == "2":
        eliminado = planillas_almacenadas.pop(idx_target)
        imprimir_exito(f"Empleado '{eliminado.empleado}' eliminado de la nómina.")

    if planillas_almacenadas:
        partida = generar_partida_contable(planillas_almacenadas)
        imprimir_partida(partida)
        return partida
    return None


def _obtener_acciones_planillas(
    planillas_almacenadas: List[ResultadoPlanilla],
    on_ingreso_interactivo: Callable[[], None],
    on_herramientas_csv: Callable[[], None],
    on_ver_partida: Callable[[], None],
    on_ver_boletas: Callable[[], None],
    on_modificar_empleado: Callable[[], None],
    on_vaciar_planilla: Callable[[], None],
) -> List[AccionMenu]:
    """Construye las acciones principales de planillas según su posición de índice."""
    acciones = [
        AccionMenu("Ingresar empleados interactivamente (Predeterminado)", on_ingreso_interactivo),
        AccionMenu("Herramientas CSV (Carga / Plantilla / Exportación)", on_herramientas_csv),
    ]
    if planillas_almacenadas:
        acciones.append(AccionMenu(f"Ver lista de empleados y boletas ({len(planillas_almacenadas)} registrados)", on_ver_boletas))
        acciones.append(AccionMenu("Modificar o eliminar empleado de la nómina", on_modificar_empleado))
        acciones.append(AccionMenu("Ver partida contable consolidada", on_ver_partida))
        acciones.append(AccionMenu("Vaciar / Reiniciar planilla actual", on_vaciar_planilla))
    return acciones


def iniciar_flujo_planillas(
    planillas_iniciales: Optional[List[ResultadoPlanilla]] = None,
) -> Tuple[List[ResultadoPlanilla], Optional[Any]]:
    """Punto de entrada interactivo principal con despacho desacoplado por índice."""
    planillas_almacenadas: List[ResultadoPlanilla] = list(planillas_iniciales) if planillas_iniciales else []
    ultima_partida = None

    imprimir_banner("SISTEMA DE PLANILLAS Y PARTIDAS CONTABLES (GUATEMALA)", border_style="cyan")

    if planillas_almacenadas:
        imprimir_aviso(f"Se cargaron {len(planillas_almacenadas)} boleta(s) de nómina previas del ejercicio.")

    def accion_ingreso() -> None:
        nonlocal ultima_partida
        nuevas = flujo_interactivo(planillas_existentes=planillas_almacenadas)
        planillas_almacenadas.clear()
        planillas_almacenadas.extend(nuevas)
        if planillas_almacenadas:
            console.print(f"\nSe han acumulado [cyan]{len(planillas_almacenadas)}[/cyan] planilla(s) en total.")
            ultima_partida = generar_partida_contable(planillas_almacenadas)
            imprimir_partida(ultima_partida)

    def accion_csv() -> None:
        nonlocal ultima_partida, planillas_almacenadas
        planillas_almacenadas = menu_herramientas_csv(planillas_almacenadas)
        if planillas_almacenadas:
            ultima_partida = generar_partida_contable(planillas_almacenadas)
            imprimir_partida(ultima_partida)

    def accion_partida() -> None:
        nonlocal ultima_partida
        if planillas_almacenadas:
            ultima_partida = generar_partida_contable(planillas_almacenadas)
            imprimir_partida(ultima_partida)

    def accion_boletas() -> None:
        _mostrar_resumen_boletas_accion(planillas_almacenadas)

    def accion_modificar() -> None:
        nonlocal ultima_partida
        resultado_partida = _modificar_o_eliminar_empleado_accion(planillas_almacenadas)
        if resultado_partida is not None:
            ultima_partida = resultado_partida
        elif not planillas_almacenadas:
            ultima_partida = None

    def accion_vaciar() -> None:
        nonlocal ultima_partida
        if pedir_confirmacion("¿Estás seguro de vaciar todos los empleados de la planilla actual? (s/n): ", default=False):
            planillas_almacenadas.clear()
            ultima_partida = None
            imprimir_exito("Planilla vaciada exitosamente.")

    while True:
        acciones = _obtener_acciones_planillas(
            planillas_almacenadas=planillas_almacenadas,
            on_ingreso_interactivo=accion_ingreso,
            on_herramientas_csv=accion_csv,
            on_ver_partida=accion_partida,
            on_ver_boletas=accion_boletas,
            on_modificar_empleado=accion_modificar,
            on_vaciar_planilla=accion_vaciar,
        )

        opciones = [(str(idx), item.descripcion) for idx, item in enumerate(acciones, start=1)]
        console.print("\n[bold]Opciones principales:[/bold]")
        imprimir_menu_opciones(opciones, texto_salir="Salir", salir_codigo=OPCION_SALIR)

        prompt_rango = f"[1-{len(acciones)}, {OPCION_SALIR}]"
        eleccion = input(f"\nSeleccione opción {prompt_rango} [1]: ").strip()

        if eleccion == OPCION_SALIR:
            console.print("\n¡Hasta pronto!")
            break

        indice_seleccionado = (
            OPCION_PREDETERMINADA_MENU
            if eleccion == ""
            else (int(eleccion) - 1 if eleccion.isdigit() else -1)
        )

        if 0 <= indice_seleccionado < len(acciones):
            acciones[indice_seleccionado].accion()
        else:
            imprimir_alerta(MENSAJE_ALERTA_OPCION)

    if planillas_almacenadas and ultima_partida is None:
        ultima_partida = generar_partida_contable(planillas_almacenadas)

    return planillas_almacenadas, ultima_partida


