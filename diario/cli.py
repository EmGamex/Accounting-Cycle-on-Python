"""Capa de presentación y menú interactivo por consola para el Libro Diario."""
from typing import Optional

from diario.asistentes import (
    registrar_apertura_asistida,
    registrar_compra_asistida,
    registrar_nomina_asistida,
    registrar_operacion_simple_asistida,
    registrar_partida_libre_asistida,
    registrar_venta_asistida,
)
from diario.engine import GestorLibroDiario
from diario.reportes import generar_texto_libro_diario


def iniciar_flujo_diario(gestor: Optional[GestorLibroDiario] = None) -> None:
    """Punto de entrada interactivo para la gestión de asientos y reportes del Libro Diario."""
    if gestor is None:
        gestor = GestorLibroDiario(estricto_cronologico=False)

    print("=" * 70)
    print("         SISTEMA DE LIBRO DIARIO CONTABLE (GUATEMALA)")
    print("=" * 70)

    while True:
        num_partidas = len(gestor.libro.partidas)
        print(f"\nLibro Diario Actual: {num_partidas} partida(s) registradas | Siguiente: Partida #{gestor.siguiente_numero}")
        print("Opciones disponibles:")
        print("  [1] Registrar Partida #1 de Apertura (Asistida / Demo)")
        print("  [2] Registrar Partida de Nómina de Sueldos (Asistida / Demo)")
        print("  [3] Registrar Compra / Gasto con IVA (Crédito Fiscal 12%)")
        print("  [4] Registrar Venta con IVA (Débito Fiscal 12%)")
        print("  [5] Registrar Operación Simple (Traslado, Cobro, Pago)")
        print("  [6] Registrar Partida Libre (Línea por línea)")
        print("  [7] Ver Libro Diario Completo")
        print("  [0] Salir")

        opcion = input("\nSeleccione una opción [1-7, 0]: ").strip()

        if opcion == "1":
            registrar_apertura_asistida(gestor)
        elif opcion == "2":
            registrar_nomina_asistida(gestor)
        elif opcion == "3":
            registrar_compra_asistida(gestor)
        elif opcion == "4":
            registrar_venta_asistida(gestor)
        elif opcion == "5":
            registrar_operacion_simple_asistida(gestor)
        elif opcion == "6":
            registrar_partida_libre_asistida(gestor)
        elif opcion == "7":
            print("\n" + generar_texto_libro_diario(gestor.libro))
        elif opcion == "0":
            print("\n¡Gracias por utilizar el Sistema de Libro Diario!")
            break
        else:
            print("  (!) Opción no reconocida. Intente nuevamente.")
