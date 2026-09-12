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

ARCHIVO_PLANTILLA_CSV_DEFAULT: str = "plantilla_empleados.csv"
OPCION_PREDETERMINADA_MENU: int = 0
OPCION_SALIR_CSV_LEGACY: str = "4"


class AccionMenu(NamedTuple):
    """Estructura para representar una opción ejecutable en el menú interactivo."""
    descripcion: str
    accion: Callable[[], Any]


def flujo_interactivo() -> List[ResultadoPlanilla]:
    """Captura secuencial de empleados desde la consola."""
    planillas: List[ResultadoPlanilla] = []
    while True:
        datos = solicitar_datos_interactivo()
        resultado = calcular_boleta(datos)
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


def _obtener_acciones_planillas(
    planillas_almacenadas: List[ResultadoPlanilla],
    on_ingreso_interactivo: Callable[[], None],
    on_herramientas_csv: Callable[[], None],
    on_ver_partida: Callable[[], None],
) -> List[AccionMenu]:
    """Construye las acciones principales de planillas según su posición de índice."""
    acciones = [
        AccionMenu("Ingresar empleados interactivamente (Predeterminado)", on_ingreso_interactivo),
        AccionMenu("Herramientas CSV (Carga / Plantilla / Exportación)", on_herramientas_csv),
    ]
    if planillas_almacenadas:
        acciones.append(AccionMenu("Ver partida contable consolidada", on_ver_partida))
    return acciones


def iniciar_flujo_planillas(
    planillas_iniciales: Optional[List[ResultadoPlanilla]] = None,
) -> Tuple[List[ResultadoPlanilla], Optional[Any]]:
    """Punto de entrada interactivo principal con despacho desacoplado por índice."""
    planillas_almacenadas: List[ResultadoPlanilla] = list(planillas_iniciales) if planillas_iniciales else []
    ultima_partida = None

    imprimir_banner("SISTEMA DE PLANILLAS Y PARTIDAS CONTABLES (GUATEMALA)", border_style="cyan")

    def accion_ingreso() -> None:
        nonlocal ultima_partida
        nuevas = flujo_interactivo()
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

    while True:
        acciones = _obtener_acciones_planillas(
            planillas_almacenadas=planillas_almacenadas,
            on_ingreso_interactivo=accion_ingreso,
            on_herramientas_csv=accion_csv,
            on_ver_partida=accion_partida,
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


