"""Punto de entrada principal para el cálculo de nómina y partidas contables."""
import sys
from typing import List

from planilla import (
    BONIFICACION_LEY,
    DEDUCCION_ISR_PERSONAL,
    IGSS_LABORAL,
    IGSS_PATRONAL,
    DatosEmpleado,
    PartidaContable,
    ResultadoPlanilla,
    calcular_boleta,
    calcular_isr_mensual,
    cargar_empleados_csv,
    crear_plantilla_csv_ejemplo,
    exportar_planilla_csv,
    generar_partida_contable,
    imprimir_boleta,
    imprimir_partida,
    money,
    solicitar_datos_interactivo,
    iniciar_flujo_planillas,
)
from planilla.cli import flujo_interactivo, menu_herramientas_csv

# Alias y compatibilidad con scripts e integraciones existentes
calcular_planilla = calcular_boleta
solicitar_datos_empleado = solicitar_datos_interactivo
main = iniciar_flujo_planillas

if __name__ == "__main__":
    try:
        iniciar_flujo_planillas()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario. Saliendo...")
        sys.exit(0)