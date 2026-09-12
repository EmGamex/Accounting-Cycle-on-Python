"""Generadores de partidas contables para operaciones comerciales frecuentes."""
from .base import crear_partida_simple
from .calculos import (
    FACTOR_BASE,
    TASA_IVA,
    TWO_PLACES,
    calcular_desglose_iva,
    distribuir_canales,
    normalizar_porcentaje,
)
from .comercial import (
    crear_partida_compra,
    crear_partida_venta,
)
from .tesoreria import (
    crear_partida_abono_cliente,
    crear_partida_abono_prestamo,
    crear_partida_abono_proveedor,
    crear_partida_deposito_banco,
    crear_partida_retiro_banco,
)

__all__ = [
    # Constantes y utilidades de cálculo
    "TWO_PLACES",
    "TASA_IVA",
    "FACTOR_BASE",
    "normalizar_porcentaje",
    "calcular_desglose_iva",
    "distribuir_canales",
    # Partidas simples
    "crear_partida_simple",
    # Ciclo comercial
    "crear_partida_venta",
    "crear_partida_compra",
    # Tesorería y cartera
    "crear_partida_abono_cliente",
    "crear_partida_abono_proveedor",
    "crear_partida_deposito_banco",
    "crear_partida_retiro_banco",
    "crear_partida_abono_prestamo",
]
