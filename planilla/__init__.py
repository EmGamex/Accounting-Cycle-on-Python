"""Paquete de gestión y cálculo de nóminas y partidas contables (Guatemala)."""
from .config import (
    BONIFICACION_LEY,
    DEDUCCION_ISR_PERSONAL,
    IGSS_LABORAL,
    IGSS_PATRONAL,
    money,
)
from .models import DatosEmpleado, PartidaContable, ResultadoPlanilla
from .calculos import calcular_boleta, calcular_isr_mensual
from .contabilidad import generar_partida_contable
from .io_handlers import (
    cargar_empleados_csv,
    crear_plantilla_csv_ejemplo,
    exportar_planilla_csv,
    imprimir_boleta,
    imprimir_partida,
    solicitar_datos_interactivo,
)

__all__ = [
    "BONIFICACION_LEY",
    "DEDUCCION_ISR_PERSONAL",
    "IGSS_LABORAL",
    "IGSS_PATRONAL",
    "money",
    "DatosEmpleado",
    "ResultadoPlanilla",
    "PartidaContable",
    "calcular_boleta",
    "calcular_isr_mensual",
    "generar_partida_contable",
    "imprimir_boleta",
    "imprimir_partida",
    "solicitar_datos_interactivo",
    "cargar_empleados_csv",
    "exportar_planilla_csv",
    "crear_plantilla_csv_ejemplo",
]
