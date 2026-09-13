"""Módulo orquestador y controlador interactivo del ciclo contable integral (Guatemala)."""
import os
from typing import Any, Callable, NamedTuple, Optional

from apertura.cli import iniciar_flujo_apertura
from planilla.cli import iniciar_flujo_planillas
from diario.cli import iniciar_flujo_diario
from diario.conectores import de_partida_apertura, de_partida_planilla
from diario.engine import GestorLibroDiario
from diario.models import TipoOrigenPartida
from mayor.cli import iniciar_flujo_mayor
from balance.cli import iniciar_flujo_balance
from persistencia import (
    EjercicioContable,
    cargar_ejercicio_json,
    guardar_ejercicio_json,
)
from config import (
    ARCHIVO_EJERCICIO_DEFAULT as CFG_ARCHIVO_EJERCICIO_DEFAULT,
    MENSAJE_ALERTA_OPCION as CFG_MENSAJE_ALERTA_OPCION,
    OPCION_SALIR as CFG_OPCION_SALIR,
    RESPUESTAS_AFIRMATIVAS as CFG_RESPUESTAS_AFIRMATIVAS,
)
from ui import (
    COLOR_SECUNDARIO,
    console,
    formatear_moneda,
    imprimir_alerta,
    imprimir_aviso,
    imprimir_banner,
    imprimir_estado_ejercicio as ui_imprimir_estado_ejercicio,
    imprimir_exito,
    imprimir_menu_opciones,
    pedir_confirmacion as ui_pedir_confirmacion,
)

# Constantes de configuración y presentación (con alias para compatibilidad y patching en tests)
ARCHIVO_EJERCICIO_DEFAULT = CFG_ARCHIVO_EJERCICIO_DEFAULT
RESPUESTAS_AFIRMATIVAS = CFG_RESPUESTAS_AFIRMATIVAS
OPCION_SALIR = CFG_OPCION_SALIR
MENSAJE_ALERTA_OPCION = CFG_MENSAJE_ALERTA_OPCION


class AccionMenu(NamedTuple):
    """Estructura para representar una opción ejecutable en un menú."""
    descripcion: str
    accion: Callable[[], Any]


def _mostrar_opciones_con_indices(acciones: list[AccionMenu], texto_salir: str = "Volver / Salir") -> None:
    """Imprime una lista de acciones numeradas secuencialmente y la opción de salida."""
    opciones = [(str(idx), item.descripcion) for idx, item in enumerate(acciones, start=1)]
    imprimir_menu_opciones(opciones, texto_salir=texto_salir, salir_codigo=OPCION_SALIR)


# ==============================================================================
# FUNCIONES AUXILIARES REUTILIZABLES
# ==============================================================================

def pedir_confirmacion(mensaje: str, default: bool = True) -> bool:
    """Solicita confirmación afirmativa o negativa al usuario de forma centralizada."""
    return ui_pedir_confirmacion(mensaje, default=default)


def asentar_partida_en_diario(gestor: GestorLibroDiario, partida_diario, tipo_nombre: str) -> None:
    """Registra una partida externa en el libro diario con número correlativo."""
    gestor.registrar_partida(partida_diario, auto_correlativo=True)
    imprimir_exito(f"Partida #{partida_diario.numero} de {tipo_nombre} asentada en el Libro Diario.")


_ejercicio_activo: EjercicioContable = EjercicioContable()


def _guardar_ejercicio(gestor: GestorLibroDiario, ruta: str) -> None:
    """Guarda las partidas del gestor y el estado del ejercicio en el archivo JSON especificado."""
    global _ejercicio_activo
    _ejercicio_activo.libro_diario = gestor.libro
    guardar_ejercicio_json(_ejercicio_activo, ruta)
    cant_partidas = len(gestor.libro.partidas)
    cant_apertura = len(_ejercicio_activo.items_apertura)
    cant_planillas = len(_ejercicio_activo.planillas)
    imprimir_exito(
        f"Ejercicio guardado exitosamente ({cant_partidas} partidas, "
        f"{cant_apertura} cuentas apertura, {cant_planillas} planillas)."
    )


def _cargar_ejercicio(gestor: GestorLibroDiario, ruta: str) -> None:
    """Carga el ejercicio desde el archivo JSON si existe."""
    if os.path.exists(ruta):
        global _ejercicio_activo
        _ejercicio_activo = cargar_ejercicio_json(ruta)
        gestor.libro = _ejercicio_activo.libro_diario
        cant_partidas = len(gestor.libro.partidas)
        cant_apertura = len(_ejercicio_activo.items_apertura)
        cant_planillas = len(_ejercicio_activo.planillas)
        imprimir_exito(
            f"Ejercicio cargado exitosamente ({cant_partidas} partidas activas, "
            f"{cant_apertura} cuentas apertura, {cant_planillas} planillas)."
        )
    else:
        imprimir_alerta(f"No se encontró el archivo '{ruta}'.")


def _guardar_personalizado(gestor: GestorLibroDiario) -> None:
    """Solicita ruta de destino y guarda el ejercicio."""
    ruta = input("Ruta o nombre del archivo JSON de destino: ").strip()
    if ruta:
        _guardar_ejercicio(gestor, ruta)


def _cargar_personalizado(gestor: GestorLibroDiario) -> None:
    """Solicita ruta de origen y carga el ejercicio."""
    ruta = input("Ruta del archivo JSON a cargar: ").strip()
    if ruta:
        _cargar_ejercicio(gestor, ruta)


# ==============================================================================
# SUBMENÚ DE PERSISTENCIA
# ==============================================================================

def _obtener_acciones_persistencia(gestor: GestorLibroDiario) -> list[AccionMenu]:
    """Retorna las acciones disponibles para el submenú de persistencia JSON."""
    return [
        AccionMenu(
            f"Guardar ejercicio actual en '{ARCHIVO_EJERCICIO_DEFAULT}'",
            lambda: _guardar_ejercicio(gestor, ARCHIVO_EJERCICIO_DEFAULT),
        ),
        AccionMenu(
            "Guardar ejercicio en una ruta personalizada",
            lambda: _guardar_personalizado(gestor),
        ),
        AccionMenu(
            f"Cargar ejercicio desde '{ARCHIVO_EJERCICIO_DEFAULT}'",
            lambda: _cargar_ejercicio(gestor, ARCHIVO_EJERCICIO_DEFAULT),
        ),
        AccionMenu(
            "Cargar ejercicio desde una ruta personalizada",
            lambda: _cargar_personalizado(gestor),
        ),
    ]


def menu_persistencia(gestor: GestorLibroDiario) -> None:
    """Submenú para guardar o cargar el ejercicio contable en formato JSON."""
    imprimir_banner("GESTIÓN Y PERSISTENCIA DEL EJERCICIO (JSON)", border_style=COLOR_SECUNDARIO)

    acciones = _obtener_acciones_persistencia(gestor)
    _mostrar_opciones_con_indices(acciones, texto_salir="Volver al menú principal")

    prompt_rango = f"[1-{len(acciones)}, {OPCION_SALIR}]"
    op = input(f"\nSeleccione una opción {prompt_rango}: ").strip()

    if op.isdigit() and 1 <= int(op) <= len(acciones):
        acciones[int(op) - 1].accion()


_menu_persistencia_core = menu_persistencia


# ==============================================================================
# ACCIONES DEL MENÚ PRINCIPAL
# ==============================================================================

def _accion_apertura(gestor: GestorLibroDiario) -> None:
    """Ejecuta el flujo de apertura y permite asentarlo en el libro diario."""
    global _ejercicio_activo
    resumen, partida_apertura = iniciar_flujo_apertura(
        cuentas_iniciales=_ejercicio_activo.items_apertura
    )
    if resumen and hasattr(resumen, "estructura_balance"):
        items = []
        for clase, subgrupos in resumen.estructura_balance.items():
            for subgrupo, cuentas in subgrupos.items():
                for cod, it in cuentas.items():
                    items.append(it)
        if items:
            _ejercicio_activo.items_apertura = items

    if partida_apertura:
        tiene_partida_1 = len(gestor.libro.partidas) > 0 and gestor.libro.partidas[0].numero == 1
        mensaje = (
            "¿Deseas actualizar la Partida #1 de Apertura en el Libro Diario?"
            if tiene_partida_1
            else "¿Deseas asentar esta Apertura como Partida #1 en el Libro Diario?"
        )
        if pedir_confirmacion(mensaje):
            num_asiento = 1 if tiene_partida_1 else gestor.siguiente_numero
            partida_diario = de_partida_apertura(partida_apertura, numero=num_asiento)
            if tiene_partida_1:
                gestor.libro.partidas[0] = partida_diario
                imprimir_exito("Partida #1 de Apertura actualizada exitosamente en el Libro Diario.")
            else:
                asentar_partida_en_diario(gestor, partida_diario, "Apertura")


def _accion_planillas(gestor: GestorLibroDiario) -> None:
    """Ejecuta el flujo de nóminas y permite asentarlo en el libro diario."""
    global _ejercicio_activo
    planillas, partida_nomina = iniciar_flujo_planillas(
        planillas_iniciales=_ejercicio_activo.planillas
    )
    if planillas:
        _ejercicio_activo.planillas = planillas

    if partida_nomina:
        idx_existente = -1
        partida_existente = None
        for idx, p in enumerate(gestor.libro.partidas):
            if p.origen == TipoOrigenPartida.PLANILLA:
                idx_existente = idx
                partida_existente = p
                break

        if partida_existente:
            mensaje = f"¿Deseas actualizar la Partida No. {partida_existente.numero} de Nómina en el Libro Diario?"
        else:
            mensaje = "¿Deseas asentar esta Nómina de Sueldos en el Libro Diario?"

        if pedir_confirmacion(mensaje):
            num_asiento = partida_existente.numero if partida_existente else gestor.siguiente_numero
            partida_diario = de_partida_planilla(partida_nomina, numero=num_asiento)
            if partida_existente:
                gestor.libro.partidas[idx_existente] = partida_diario
                imprimir_exito(f"Partida No. {num_asiento} de Nómina actualizada exitosamente en el Libro Diario.")
            else:
                asentar_partida_en_diario(gestor, partida_diario, "Nómina")


def _accion_salir(gestor: GestorLibroDiario) -> None:
    """Gestiona el guardado preventivo y mensaje de despedida antes de salir."""
    if gestor.libro.partidas:
        pregunta = f"¿Deseas guardar los cambios en '{ARCHIVO_EJERCICIO_DEFAULT}' antes de salir?"
        if pedir_confirmacion(pregunta):
            try:
                _guardar_ejercicio(gestor, ARCHIVO_EJERCICIO_DEFAULT)
            except Exception as e:
                imprimir_alerta(f"Error al guardar ejercicio: {e}")
    console.print("\n[bold green]¡Gracias por utilizar el Sistema Contable Integral! Hasta pronto.[/bold green]")


def _imprimir_banner_principal() -> None:
    """Imprime el banner del menú principal del sistema."""
    imprimir_banner("SISTEMA CONTABLE INTEGRAL (GUATEMALA)")


def _imprimir_estado_ejercicio(gestor: GestorLibroDiario) -> None:
    """Muestra el balance y cuadre actual del libro diario."""
    total_d, total_h = gestor.totales()
    cuadra = gestor.libro.cuadra or not gestor.libro.partidas
    ui_imprimir_estado_ejercicio(len(gestor.libro.partidas), total_d, total_h, cuadra)


def _obtener_acciones_principales(gestor: GestorLibroDiario) -> list[AccionMenu]:
    """Retorna los módulos principales disponibles en el orquestador."""
    return [
        AccionMenu(
            "Sistema de Apertura Contable (Inventario y Balance Inicial)",
            lambda: _accion_apertura(gestor),
        ),
        AccionMenu(
            "Sistema de Planillas y Nóminas (Cálculo de Sueldos y Boletas)",
            lambda: _accion_planillas(gestor),
        ),
        AccionMenu(
            "Sistema de Libro Diario (Registro de Operaciones Diarias)",
            lambda: iniciar_flujo_diario(gestor=gestor),
        ),
        AccionMenu(
            "Sistema de Libro Mayor y T-Gráficas (Pases y Saldos)",
            lambda: iniciar_flujo_mayor(gestor_diario=gestor),
        ),
        AccionMenu(
            "Sistema de Balances (4 Columnas y Situación General de Cierre)",
            lambda: iniciar_flujo_balance(gestor_diario=gestor),
        ),
        AccionMenu(
            "Guardar / Cargar Ejercicio Contable (Persistencia JSON)",
            lambda: menu_persistencia(gestor),
        ),
    ]


# ==============================================================================
# ORQUESTADOR PRINCIPAL
# ==============================================================================

def menu_principal(
    gestor: Optional[GestorLibroDiario] = None,
    ejercicio: Optional[EjercicioContable] = None,
) -> None:
    """Orquestador interactivo para la ejecución de módulos del ciclo contable con estado unificado."""
    global _ejercicio_activo
    if ejercicio is not None:
        _ejercicio_activo = ejercicio

    if gestor is None:
        gestor = GestorLibroDiario(estricto_cronologico=False)
        if os.path.exists(ARCHIVO_EJERCICIO_DEFAULT):
            try:
                _ejercicio_activo = cargar_ejercicio_json(ARCHIVO_EJERCICIO_DEFAULT)
                gestor.libro = _ejercicio_activo.libro_diario
            except Exception:
                pass
        else:
            _ejercicio_activo.libro_diario = gestor.libro
    else:
        _ejercicio_activo.libro_diario = gestor.libro

    _imprimir_banner_principal()

    while True:
        _imprimir_estado_ejercicio(gestor)
        acciones = _obtener_acciones_principales(gestor)

        console.print("\nMódulos principales disponibles:")
        _mostrar_opciones_con_indices(acciones, texto_salir="Salir")

        prompt_rango = f"[1-{len(acciones)}, {OPCION_SALIR}]"
        opcion = input(f"\nSeleccione una opción {prompt_rango}: ").strip()

        if opcion == OPCION_SALIR:
            _accion_salir(gestor)
            break

        if opcion.isdigit() and 1 <= int(opcion) <= len(acciones):
            try:
                acciones[int(opcion) - 1].accion()
            except KeyboardInterrupt:
                imprimir_aviso("Retornando al menú principal...")
        else:
            imprimir_alerta(MENSAJE_ALERTA_OPCION)
