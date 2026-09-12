"""Módulo de Balance de Comprobación y Situación General de Cierre."""
from .engine import (
    GestorBalance,
    calcular_estado_resultados,
    generar_balance_4_columnas,
    generar_balance_general,
)
from .exceptions import (
    BalanceError,
    BalanceVacioError,
    DescuadreBalanceError,
    EcuacionPatrimonialError,
)
from .models import (
    Balance4Columnas,
    BalanceSituacionGeneral,
    FilaBalance4Columnas,
    ItemBalanceGeneral,
    ResumenResultados,
)


def iniciar_flujo_balance(*args, **kwargs):
    """Carga perezosa del flujo de CLI para evitar importaciones circulares."""
    from .cli import iniciar_flujo_balance as _iniciar
    return _iniciar(*args, **kwargs)


__all__ = [
    "Balance4Columnas",
    "BalanceError",
    "BalanceSituacionGeneral",
    "BalanceVacioError",
    "DescuadreBalanceError",
    "EcuacionPatrimonialError",
    "FilaBalance4Columnas",
    "GestorBalance",
    "ItemBalanceGeneral",
    "ResumenResultados",
    "calcular_estado_resultados",
    "generar_balance_4_columnas",
    "generar_balance_general",
    "iniciar_flujo_balance",
]
