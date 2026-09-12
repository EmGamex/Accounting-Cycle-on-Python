"""Generador base para partidas contables simétricas de doble columna."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from ..models import MovimientoLinea, PartidaDiario, TipoOrigenPartida
from .calculos import TWO_PLACES


def crear_partida_simple(
    numero: int,
    fecha: date,
    glosa: str,
    monto: Decimal,
    codigo_debe: str,
    nombre_debe: str,
    codigo_haber: str,
    nombre_haber: str,
    origen: TipoOrigenPartida = TipoOrigenPartida.OPERACION,
    documento_soporte: Optional[str] = None,
) -> PartidaDiario:
    """Crea una partida simple de dos líneas (un cargo y un abono por importes iguales)."""
    if not isinstance(monto, Decimal):
        monto = Decimal(str(monto))
    monto_val = monto.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    lineas = [
        MovimientoLinea(codigo=codigo_debe, nombre=nombre_debe, debe=monto_val, haber=Decimal("0.00")),
        MovimientoLinea(codigo=codigo_haber, nombre=nombre_haber, debe=Decimal("0.00"), haber=monto_val),
    ]

    return PartidaDiario(
        numero=numero,
        fecha=fecha,
        glosa=glosa,
        lineas=lineas,
        origen=origen,
        documento_soporte=documento_soporte,
    )
