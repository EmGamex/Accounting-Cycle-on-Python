"""Configuración y parámetros legales del sistema de nómina guatemalteco."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Union

import config as global_config

# Constantes legales y porcentajes (Guatemala) - sincronizados con config global
IGSS_LABORAL: Decimal = getattr(global_config, "TASA_IGSS_LABORAL", Decimal("0.0483"))
IGSS_PATRONAL: Decimal = getattr(global_config, "TASA_IGSS_PATRONAL", Decimal("0.1267"))
BONIFICACION_LEY: Decimal = getattr(global_config, "BONIFICACION_INCENTIVO", Decimal("250.00"))
DEDUCCION_ISR_PERSONAL: Decimal = Decimal("48000.00")  # Gastos personales sin comprobación anual

# Tramos de ISR sobre rentas de trabajo (Decreto 10-2012)
TRAMO_ISR_5_MAX: Decimal = Decimal("300000.00")
TASA_ISR_5: Decimal = Decimal("0.05")
TASA_ISR_7: Decimal = Decimal("0.07")
IMPORTE_FIJO_ISR_7: Decimal = Decimal("15000.00")

# Provisiones de pasivo laboral mensual
PROVISION_AGUINALDO: Decimal = getattr(global_config, "PROVISION_AGUINALDO", Decimal("0.0833"))
PROVISION_BONO_14: Decimal = getattr(global_config, "PROVISION_BONO_14", Decimal("0.0833"))
PROVISION_VACACIONES: Decimal = getattr(global_config, "PROVISION_VACACIONES", Decimal("0.0417"))
PROVISION_INDEMNIZACION: Decimal = getattr(global_config, "PROVISION_INDEMNIZACION", Decimal("0.0833"))

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
