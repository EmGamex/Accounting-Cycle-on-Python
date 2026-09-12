"""Capa de presentación y menú interactivo por consola para el cálculo de nómina y planillas."""
from typing import Any, List, Optional, Tuple

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


def menu_herramientas_csv(planillas_actuales: List[ResultadoPlanilla]) -> List[ResultadoPlanilla]:
    """Menú secundario para carga o exportación de archivos CSV (opción a futuro)."""
    imprimir_banner("HERRAMIENTAS CSV (OPCIONALES)", border_style="blue")
    opciones = [
        ("1", "Generar archivo 'plantilla_empleados.csv' de ejemplo"),
        ("2", "Cargar y procesar empleados desde un archivo CSV"),
    ]
    if planillas_actuales:
        opciones.append(("3", f"Exportar planillas actuales a '{ARCHIVO_PLANILLA_DEFAULT}'"))

    imprimir_menu_opciones(opciones, texto_salir="Volver al menú principal", salir_codigo=OPCION_SALIR)

    prompt_rango = f"[1-{len(opciones)}, {OPCION_SALIR}]"
    opcion = input(f"\nSeleccione una opción {prompt_rango}: ").strip()

    if opcion in (OPCION_SALIR, "4"):
        return planillas_actuales
    elif opcion == "1":
        ruta = input("Nombre o ruta del archivo [plantilla_empleados.csv]: ").strip() or "plantilla_empleados.csv"
        crear_plantilla_csv_ejemplo(ruta)
        imprimir_exito(f"Plantilla generada exitosamente en: {ruta}")
    elif opcion == "2":
        ruta = input("Ruta del archivo CSV a cargar: ").strip()
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
    elif opcion == "3" and planillas_actuales:
        ruta = input(f"Nombre de archivo de destino [{ARCHIVO_PLANILLA_DEFAULT}]: ").strip() or ARCHIVO_PLANILLA_DEFAULT
        exportar_planilla_csv(planillas_actuales, ruta)
        imprimir_exito(f"Planilla exportada exitosamente en: {ruta}")
    else:
        imprimir_alerta(MENSAJE_ALERTA_OPCION)

    return planillas_actuales


def _mostrar_menu_planillas(planillas_almacenadas: List[ResultadoPlanilla]) -> List[Tuple[str, str]]:
    """Muestra el menú principal de operaciones de nóminas."""
    console.print("\n[bold]Opciones principales:[/bold]")
    opciones = [
        ("1", "Ingresar empleados interactivamente (Predeterminado)"),
        ("2", "Herramientas CSV (Carga / Plantilla / Exportación)"),
    ]
    if planillas_almacenadas:
        opciones.append(("3", "Ver partida contable consolidada"))
    imprimir_menu_opciones(opciones, texto_salir="Salir", salir_codigo=OPCION_SALIR)
    return opciones


def iniciar_flujo_planillas(
    planillas_iniciales: Optional[List[ResultadoPlanilla]] = None,
) -> Tuple[List[ResultadoPlanilla], Optional[Any]]:
    """Punto de entrada interactivo principal para la gestión y cálculo de nóminas."""
    planillas_almacenadas: List[ResultadoPlanilla] = list(planillas_iniciales) if planillas_iniciales else []
    ultima_partida = None

    imprimir_banner("SISTEMA DE PLANILLAS Y PARTIDAS CONTABLES (GUATEMALA)", border_style="cyan")

    while True:
        opciones = _mostrar_menu_planillas(planillas_almacenadas)

        prompt_rango = f"[1-{len(opciones)}, {OPCION_SALIR}]"
        eleccion = input(f"\nSeleccione opción {prompt_rango} [1]: ").strip()

        if eleccion in ("1", ""):
            nuevas = flujo_interactivo()
            planillas_almacenadas.extend(nuevas)
            if planillas_almacenadas:
                console.print(f"\nSe han acumulado [cyan]{len(planillas_almacenadas)}[/cyan] planilla(s) en total.")
                ultima_partida = generar_partida_contable(planillas_almacenadas)
                imprimir_partida(ultima_partida)
        elif eleccion == "2":
            planillas_almacenadas = menu_herramientas_csv(planillas_almacenadas)
            if planillas_almacenadas:
                ultima_partida = generar_partida_contable(planillas_almacenadas)
                imprimir_partida(ultima_partida)
        elif eleccion == "3" and planillas_almacenadas:
            ultima_partida = generar_partida_contable(planillas_almacenadas)
            imprimir_partida(ultima_partida)
        elif eleccion == OPCION_SALIR:
            console.print("\n¡Hasta pronto!")
            break
        else:
            imprimir_alerta(MENSAJE_ALERTA_OPCION)

    if planillas_almacenadas and ultima_partida is None:
        ultima_partida = generar_partida_contable(planillas_almacenadas)

    return planillas_almacenadas, ultima_partida

