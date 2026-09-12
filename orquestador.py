"""Módulo orquestador y controlador interactivo del ciclo contable integral (Guatemala)."""
import os
from typing import Callable, Optional

from apertura.cli import iniciar_flujo_apertura
from planilla.cli import iniciar_flujo_planillas
from diario.cli import iniciar_flujo_diario
from diario.conectores import de_partida_apertura, de_partida_planilla
from diario.engine import GestorLibroDiario

# Constantes de configuración y persistencia
ARCHIVO_EJERCICIO_DEFAULT = "libro_diario.json"
ANCHO_ENCABEZADO = 72
ANCHO_SUBMENU = 55
RESPUESTAS_AFIRMATIVAS = ("s", "si", "y", "yes", "")

# Opciones del menú principal
OPCION_APERTURA = "1"
OPCION_PLANILLAS = "2"
OPCION_DIARIO = "3"
OPCION_PERSISTENCIA = "4"
OPCION_SALIR = "0"

# Opciones del submenú de persistencia
OPCION_PERSISTENCIA_GUARDAR_DEFAULT = "1"
OPCION_PERSISTENCIA_GUARDAR_CUSTOM = "2"
OPCION_PERSISTENCIA_CARGAR_DEFAULT = "3"
OPCION_PERSISTENCIA_CARGAR_CUSTOM = "4"
OPCION_PERSISTENCIA_VOLVER = "0"


# ==============================================================================
# FUNCIONES AUXILIARES REUTILIZABLES
# ==============================================================================

def pedir_confirmacion(mensaje: str, default: bool = True) -> bool:
    """Solicita confirmación afirmativa o negativa al usuario."""
    sufijo = " [s]: " if default else " [n]: "
    resp = input(f"\n{mensaje} (s/n){sufijo}").strip().lower()
    if default:
        return resp in RESPUESTAS_AFIRMATIVAS
    return resp in ("s", "si", "y", "yes")


def asentar_partida_en_diario(gestor: GestorLibroDiario, partida_diario, tipo_nombre: str) -> None:
    """Registra una partida externa en el libro diario con número correlativo."""
    gestor.registrar_partida(partida_diario, auto_correlativo=True)
    print(f"  [OK] Partida #{partida_diario.numero} de {tipo_nombre} asentada en el Libro Diario.")


def _guardar_ejercicio(gestor: GestorLibroDiario, ruta: str) -> None:
    """Guarda las partidas del gestor en el archivo JSON especificado."""
    gestor.guardar_json(ruta)
    print(f"  [OK] Ejercicio guardado exitosamente ({len(gestor.libro.partidas)} partidas).")


def _cargar_ejercicio(gestor: GestorLibroDiario, ruta: str) -> None:
    """Carga las partidas desde el archivo JSON si existe."""
    if os.path.exists(ruta):
        gestor.cargar_json(ruta)
        print(f"  [OK] Ejercicio cargado exitosamente ({len(gestor.libro.partidas)} partidas activas).")
    else:
        print(f"  (!) No se encontró el archivo '{ruta}'.")


def _guardar_personalizado(gestor: GestorLibroDiario) -> None:
    """Solicita ruta de destino y guarda el ejercicio."""
    ruta = input("Ruta o nombre del archivo JSON de destino: ").strip()
    if ruta:
        gestor.guardar_json(ruta)
        print(f"  [OK] Ejercicio guardado exitosamente en '{ruta}'.")


def _cargar_personalizado(gestor: GestorLibroDiario) -> None:
    """Solicita ruta de origen y carga el ejercicio."""
    ruta = input("Ruta del archivo JSON a cargar: ").strip()
    if ruta:
        _cargar_ejercicio(gestor, ruta)


# ==============================================================================
# SUBMENÚ DE PERSISTENCIA
# ==============================================================================

def menu_persistencia(gestor: GestorLibroDiario) -> None:
    """Submenú para guardar o cargar el ejercicio contable en formato JSON."""
    print("\n" + "-" * ANCHO_SUBMENU)
    print("      GESTIÓN Y PERSISTENCIA DEL EJERCICIO (JSON)")
    print("-" * ANCHO_SUBMENU)
    print(f"  [{OPCION_PERSISTENCIA_GUARDAR_DEFAULT}] Guardar ejercicio actual en '{ARCHIVO_EJERCICIO_DEFAULT}'")
    print(f"  [{OPCION_PERSISTENCIA_GUARDAR_CUSTOM}] Guardar ejercicio en una ruta personalizada")
    print(f"  [{OPCION_PERSISTENCIA_CARGAR_DEFAULT}] Cargar ejercicio desde '{ARCHIVO_EJERCICIO_DEFAULT}'")
    print(f"  [{OPCION_PERSISTENCIA_CARGAR_CUSTOM}] Cargar ejercicio desde una ruta personalizada")
    print(f"  [{OPCION_PERSISTENCIA_VOLVER}] Volver al menú principal")

    op = input(
        f"\nSeleccione una opción [{OPCION_PERSISTENCIA_GUARDAR_DEFAULT}-{OPCION_PERSISTENCIA_CARGAR_CUSTOM}, "
        f"{OPCION_PERSISTENCIA_VOLVER}]: "
    ).strip()

    acciones: dict[str, Callable[[], None]] = {
        OPCION_PERSISTENCIA_GUARDAR_DEFAULT: lambda: _guardar_ejercicio(gestor, ARCHIVO_EJERCICIO_DEFAULT),
        OPCION_PERSISTENCIA_GUARDAR_CUSTOM: lambda: _guardar_personalizado(gestor),
        OPCION_PERSISTENCIA_CARGAR_DEFAULT: lambda: _cargar_ejercicio(gestor, ARCHIVO_EJERCICIO_DEFAULT),
        OPCION_PERSISTENCIA_CARGAR_CUSTOM: lambda: _cargar_personalizado(gestor),
    }

    accion = acciones.get(op)
    if accion:
        accion()


_menu_persistencia_core = menu_persistencia


# ==============================================================================
# ACCIONES DEL MENÚ PRINCIPAL
# ==============================================================================

def _accion_apertura(gestor: GestorLibroDiario) -> None:
    """Ejecuta el flujo de apertura y permite asentarlo en el libro diario."""
    _, partida_apertura = iniciar_flujo_apertura()
    if partida_apertura and pedir_confirmacion("¿Deseas asentar esta Apertura como Partida #1 en el Libro Diario?"):
        partida_diario = de_partida_apertura(partida_apertura, numero=gestor.siguiente_numero)
        asentar_partida_en_diario(gestor, partida_diario, "Apertura")


def _accion_planillas(gestor: GestorLibroDiario) -> None:
    """Ejecuta el flujo de nóminas y permite asentarlo en el libro diario."""
    _, partida_nomina = iniciar_flujo_planillas()
    if partida_nomina and pedir_confirmacion("¿Deseas asentar esta Nómina de Sueldos en el Libro Diario?"):
        partida_diario = de_partida_planilla(partida_nomina, numero=gestor.siguiente_numero)
        asentar_partida_en_diario(gestor, partida_diario, "Nómina")


def _accion_salir(gestor: GestorLibroDiario) -> None:
    """Gestiona el guardado preventivo y mensaje de despedida antes de salir."""
    if gestor.libro.partidas:
        pregunta = f"¿Deseas guardar los cambios en '{ARCHIVO_EJERCICIO_DEFAULT}' antes de salir?"
        if pedir_confirmacion(pregunta):
            try:
                gestor.guardar_json(ARCHIVO_EJERCICIO_DEFAULT)
                print(f"  [OK] Ejercicio guardado exitosamente en '{ARCHIVO_EJERCICIO_DEFAULT}'.")
            except Exception as e:
                print(f"  (!) Error al guardar ejercicio: {e}")
    print("\n¡Gracias por utilizar el Sistema Contable Integral! Hasta pronto.")


# ==============================================================================
# ORQUESTADOR PRINCIPAL
# ==============================================================================

def menu_principal(gestor: Optional[GestorLibroDiario] = None) -> None:
    """Orquestador interactivo para la ejecución de módulos del ciclo contable con estado unificado."""
    if gestor is None:
        gestor = GestorLibroDiario(estricto_cronologico=False)
        if os.path.exists(ARCHIVO_EJERCICIO_DEFAULT):
            try:
                gestor.cargar_json(ARCHIVO_EJERCICIO_DEFAULT)
            except Exception:
                pass

    print("=" * ANCHO_ENCABEZADO)
    print("             SISTEMA CONTABLE INTEGRAL (GUATEMALA)")
    print("=" * ANCHO_ENCABEZADO)

    acciones: dict[str, Callable[[], None]] = {
        OPCION_APERTURA: lambda: _accion_apertura(gestor),
        OPCION_PLANILLAS: lambda: _accion_planillas(gestor),
        OPCION_DIARIO: lambda: iniciar_flujo_diario(gestor=gestor),
        OPCION_PERSISTENCIA: lambda: menu_persistencia(gestor),
    }

    while True:
        total_d, total_h = gestor.totales()
        cuadra_str = "CUADRADO" if gestor.libro.cuadra or not gestor.libro.partidas else "DESCUADRADO"
        print(f"\nEstado del Ejercicio: {len(gestor.libro.partidas)} partida(s) en Diario | "
              f"Debe: Q{total_d:,.2f} | Haber: Q{total_h:,.2f} [{cuadra_str}]")

        print("\nMódulos principales disponibles:")
        print(f"  [{OPCION_APERTURA}] Sistema de Apertura Contable (Inventario y Balance Inicial)")
        print(f"  [{OPCION_PLANILLAS}] Sistema de Planillas y Nóminas (Cálculo de Sueldos y Boletas)")
        print(f"  [{OPCION_DIARIO}] Sistema de Libro Diario (Registro de Operaciones Diarias)")
        print(f"  [{OPCION_PERSISTENCIA}] Guardar / Cargar Ejercicio Contable (Persistencia JSON)")
        print(f"  [{OPCION_SALIR}] Salir")

        opcion = input(f"\nSeleccione una opción [{OPCION_APERTURA}-{OPCION_PERSISTENCIA}, {OPCION_SALIR}]: ").strip()

        if opcion == OPCION_SALIR:
            _accion_salir(gestor)
            break

        accion = acciones.get(opcion)
        if accion:
            try:
                accion()
            except KeyboardInterrupt:
                print("\n  [!] Retornando al menú principal...")
        else:
            print("  (!) Opción no reconocida. Intente nuevamente.")
