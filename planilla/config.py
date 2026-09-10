"""Configuración y parámetros legales del sistema de nómina guatemalteco."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Union

# Constantes legales y porcentajes (Guatemala)
IGSS_LABORAL: Decimal = Decimal("0.0483")      # Cuota laboral 4.83%
IGSS_PATRONAL: Decimal = Decimal("0.1267")     # 10.67% IGSS + 1.00% IRTRA + 1.00% INTECAP = 12.67%
BONIFICACION_LEY: Decimal = Decimal("250.00")  # Bonificación Incentivo Decreto 78-89
DEDUCCION_ISR_PERSONAL: Decimal = Decimal("48000.00")  # Gastos personales sin comprobación anual

# Tramos de ISR sobre rentas de trabajo (Decreto 10-2012)
TRAMO_ISR_5_MAX: Decimal = Decimal("300000.00")
TASA_ISR_5: Decimal = Decimal("0.05")
TASA_ISR_7: Decimal = Decimal("0.07")
IMPORTE_FIJO_ISR_7: Decimal = Decimal("15000.00")

# Provisiones de pasivo laboral mensual
PROVISION_AGUINALDO: Decimal = Decimal("0.0833")       # 1/12
PROVISION_BONO_14: Decimal = Decimal("0.0833")         # 1/12
PROVISION_VACACIONES: Decimal = Decimal("0.0417")      # 15 días / 360
PROVISION_INDEMNIZACION: Decimal = Decimal("0.0833")   # 1/12

# Factores de tiempo
DIAS_MES_COMERCIAL: Decimal = Decimal("30")
RECARGO_HORA_EXTRA: Decimal = Decimal("1.5")


def money(valor: Union[Decimal, float, int, str]) -> Decimal:
    """Convierte cualquier valor a Decimal y lo redondea a 2 decimales (ROUND_HALF_UP)."""
    if valor is None:
        return Decimal("0.00")
    if isinstance(valor, float):
        return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
