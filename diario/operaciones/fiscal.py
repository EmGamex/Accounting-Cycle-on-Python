"""Operaciones contables de regularización y liquidación del IVA (Guatemala)."""
from datetime import date
from decimal import Decimal
from typing import Optional, Tuple

from config import CERO_MONETARIO
from catalogo_contable import Cuenta
from ..models import PartidaDiario, TipoOrigenPartida
from .base import crear_partida_simple
from .calculos import TWO_PLACES

# Constantes del dominio fiscal y de regularización
COD_IVA_DEBITO: str = Cuenta.IVA_DEBITO.value
COD_IVA_CREDITO: str = Cuenta.IVA_CREDITO.value
NOMBRE_IVA_DEBITO: str = "IVA por Pagar"
NOMBRE_IVA_CREDITO: str = "Crédito Fiscal"
DOC_SOPORTE_REGULARIZACION: str = "REG-IVA"

TIPO_RESULTADO_PAGAR: str = "PAGAR"
TIPO_RESULTADO_FAVOR: str = "FAVOR"
TIPO_RESULTADO_CERO: str = "CERO"

GLOSA_REGULARIZACION_DEFAULT: str = (
    "Regularización del IVA correspondiente a las operaciones del período "
    "(compensación de Débito Fiscal contra Crédito Fiscal)."
)


def calcular_regularizacion_iva(
    saldo_credito: Decimal,
    saldo_debito: Decimal,
) -> Tuple[Decimal, Decimal, str]:
    """Determina el importe a compensar y la situación tributaria resultante.

    Args:
        saldo_credito: Saldo deudor acumulado en Crédito Fiscal (1107).
        saldo_debito: Saldo acreedor acumulado en Débito Fiscal (2105).

    Returns:
        Tupla (monto_compensar, saldo_remanente, tipo_resultado):
        - monto_compensar: Monto menor a liquidar en ambas cuentas.
        - saldo_remanente: Diferencia neta tras la liquidación.
        - tipo_resultado: "PAGAR" (a favor SAT), "FAVOR" (crédito retenido), o "CERO".
    """
    if not isinstance(saldo_credito, Decimal):
        saldo_credito = Decimal(str(saldo_credito))
    if not isinstance(saldo_debito, Decimal):
        saldo_debito = Decimal(str(saldo_debito))

    credito = max(CERO_MONETARIO, saldo_credito).quantize(TWO_PLACES)
    debito = max(CERO_MONETARIO, saldo_debito).quantize(TWO_PLACES)

    monto_compensar = min(credito, debito).quantize(TWO_PLACES)
    diferencia = abs(debito - credito).quantize(TWO_PLACES)

    if debito > credito:
        tipo = TIPO_RESULTADO_PAGAR
    elif credito > debito:
        tipo = TIPO_RESULTADO_FAVOR
    else:
        tipo = TIPO_RESULTADO_CERO

    return monto_compensar, diferencia, tipo


def crear_partida_regularizacion_iva(
    numero: int,
    fecha: date,
    monto: Decimal,
    glosa: Optional[str] = None,
    documento_soporte: Optional[str] = None,
) -> PartidaDiario:
    """Genera una partida simétrica que debita IVA Débito (2105) y acredita IVA Crédito (1107).

    Args:
        numero: Correlativo formal del Libro Diario.
        fecha: Fecha contable del asiento.
        monto: Importe a compensar entre ambas cuentas.
        glosa: Explicación del asiento contable.
        documento_soporte: Identificador de respaldo (e.g., 'REG-IVA').

    Returns:
        PartidaDiario formal con tipo de origen AJUSTE.
    """
    glosa_final = glosa.strip() if glosa and glosa.strip() else GLOSA_REGULARIZACION_DEFAULT
    return crear_partida_simple(
        numero=numero,
        fecha=fecha,
        glosa=glosa_final,
        monto=monto,
        codigo_debe=COD_IVA_DEBITO,
        nombre_debe=NOMBRE_IVA_DEBITO,
        codigo_haber=COD_IVA_CREDITO,
        nombre_haber=NOMBRE_IVA_CREDITO,
        origen=TipoOrigenPartida.AJUSTE,
        documento_soporte=documento_soporte or DOC_SOPORTE_REGULARIZACION,
    )
