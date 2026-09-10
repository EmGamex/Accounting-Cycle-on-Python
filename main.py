"""Punto de entrada principal y unificado para el Sistema Contable Integral (Guatemala)."""
import os
import sys
from typing import Optional

from apertura.cli import iniciar_flujo_apertura
from planilla.cli import iniciar_flujo_planillas
from diario.cli import iniciar_flujo_diario
from diario.conectores import de_partida_apertura, de_partida_planilla
from diario.engine import GestorLibroDiario

ARCHIVO_EJERCICIO_DEFAULT = "libro_diario.json"


def menu_persistencia(gestor: GestorLibroDiario) -> None:
    """Submenú para guardar o cargar el ejercicio contable en formato JSON."""
    print("\n" + "-" * 55)
    print("      GESTIÓN Y PERSISTENCIA DEL EJERCICIO (JSON)")
    print("-" * 55)
    print(f"  [1] Guardar ejercicio actual en '{ARCHIVO_EJERCICIO_DEFAULT}'")
    print("  [2] Guardar ejercicio en una ruta personalizada")
    print(f"  [3] Cargar ejercicio desde '{ARCHIVO_EJERCICIO_DEFAULT}'")
    print("  [4] Cargar ejercicio desde una ruta personalizada")
    print("  [0] Volver al menú principal")

    op = input("\nSeleccione una opción [1-4, 0]: ").strip()
    if op == "1":
        gestor.guardar_json(ARCHIVO_EJERCICIO_DEFAULT)
        print(f"  [OK] Ejercicio guardado exitosamente ({len(gestor.libro.partidas)} partidas).")
    elif op == "2":
        ruta = input("Ruta o nombre del archivo JSON de destino: ").strip()
        if ruta:
            gestor.guardar_json(ruta)
            print(f"  [OK] Ejercicio guardado exitosamente en '{ruta}'.")
    elif op == "3":
        if os.path.exists(ARCHIVO_EJERCICIO_DEFAULT):
            gestor.cargar_json(ARCHIVO_EJERCICIO_DEFAULT)
            print(f"  [OK] Ejercicio cargado exitosamente ({len(gestor.libro.partidas)} partidas activas).")
        else:
            print(f"  (!) El archivo '{ARCHIVO_EJERCICIO_DEFAULT}' no existe actualmente.")
    elif op == "4":
        ruta = input("Ruta del archivo JSON a cargar: ").strip()
        if os.path.exists(ruta):
            gestor.cargar_json(ruta)
            print(f"  [OK] Ejercicio cargado exitosamente ({len(gestor.libro.partidas)} partidas activas).")
        else:
            print(f"  (!) No se encontró el archivo '{ruta}'.")


def menu_principal(gestor: Optional[GestorLibroDiario] = None) -> None:
    """Orquestador interactivo para la ejecución de módulos del ciclo contable con estado unificado."""
    if gestor is None:
        gestor = GestorLibroDiario(estricto_cronologico=False)
        if os.path.exists(ARCHIVO_EJERCICIO_DEFAULT):
            try:
                gestor.cargar_json(ARCHIVO_EJERCICIO_DEFAULT)
            except Exception:
                pass

    print("=" * 72)
    print("             SISTEMA CONTABLE INTEGRAL (GUATEMALA)")
    print("=" * 72)

    while True:
        total_d, total_h = gestor.totales()
        cuadra_str = "CUADRADO" if gestor.libro.cuadra or len(gestor.libro.partidas) == 0 else "DESCUADRADO"
        print(f"\nEstado del Ejercicio: {len(gestor.libro.partidas)} partida(s) en Diario | "
              f"Debe: Q{total_d:,.2f} | Haber: Q{total_h:,.2f} [{cuadra_str}]")

        print("\nMódulos principales disponibles:")
        print("  [1] Sistema de Apertura Contable (Inventario y Balance Inicial)")
        print("  [2] Sistema de Planillas y Nóminas (Cálculo de Sueldos y Boletas)")
        print("  [3] Sistema de Libro Diario (Registro de Operaciones Diarias)")
        print("  [4] Guardar / Cargar Ejercicio Contable (Persistencia JSON)")
        print("  [0] Salir")

        opcion = input("\nSeleccione una opción [1-4, 0]: ").strip()

        if opcion == "1":
            try:
                resumen, partida_apertura = iniciar_flujo_apertura()
                if partida_apertura:
                    resp = input("\n¿Deseas asentar esta Apertura como Partida #1 en el Libro Diario? (s/n) [s]: ").strip().lower()
                    if resp in ("s", "si", "y", "yes", ""):
                        partida_diario = de_partida_apertura(partida_apertura, numero=gestor.siguiente_numero)
                        gestor.registrar_partida(partida_diario, auto_correlativo=True)
                        print(f"  [OK] Partida #{partida_diario.numero} de Apertura asentada en el Libro Diario.")
            except KeyboardInterrupt:
                print("\n  [!] Retornando al menú principal...")
        elif opcion == "2":
            try:
                _, partida_nomina = iniciar_flujo_planillas()
                if partida_nomina:
                    resp = input("\n¿Deseas asentar esta Nómina de Sueldos en el Libro Diario? (s/n) [s]: ").strip().lower()
                    if resp in ("s", "si", "y", "yes", ""):
                        partida_diario = de_partida_planilla(partida_nomina, numero=gestor.siguiente_numero)
                        gestor.registrar_partida(partida_diario, auto_correlativo=True)
                        print(f"  [OK] Partida #{partida_diario.numero} de Nómina asentada en el Libro Diario.")
            except KeyboardInterrupt:
                print("\n  [!] Retornando al menú principal...")
        elif opcion == "3":
            try:
                iniciar_flujo_diario(gestor=gestor)
            except KeyboardInterrupt:
                print("\n  [!] Retornando al menú principal...")
        elif opcion == "4":
            try:
                menu_persistencia(gestor)
            except KeyboardInterrupt:
                print("\n  [!] Retornando al menú principal...")
        elif opcion == "0":
            if gestor.libro.partidas:
                guardar_auto = input(f"\n¿Deseas guardar los cambios en '{ARCHIVO_EJERCICIO_DEFAULT}' antes de salir? (s/n) [s]: ").strip().lower()
                if guardar_auto in ("s", "si", "y", "yes", ""):
                    try:
                        gestor.guardar_json(ARCHIVO_EJERCICIO_DEFAULT)
                        print(f"  [OK] Ejercicio guardado exitosamente en '{ARCHIVO_EJERCICIO_DEFAULT}'.")
                    except Exception as e:
                        print(f"  (!) Error al guardar ejercicio: {e}")
            print("\n¡Gracias por utilizar el Sistema Contable Integral! Hasta pronto.")
            break
        else:
            print("  (!) Opción no reconocida. Intente nuevamente.")


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\nSesión finalizada por el usuario. Saliendo...")
        sys.exit(0)