"""Generadores de partidas de tesorería, cobros, pagos y préstamos."""
from datetime import date
from decimal import Decimal
from typing import Optional

from ..models import PartidaDiario, TipoOrigenPartida
from .base import crear_partida_simple


def crear_partida_abono_cliente(
    numero: int,
    fecha: date,
    monto: Decimal,
    medio: str = "caja",  # 'caja' o 'banco'
    glosa: Optional[str] = None,
    documento_soporte: Optional[str] = None,
) -> PartidaDiario:
    """Registra un cobro / abono de clientes a su saldo pendiente."""
    medio_lower = medio.strip().lower()
    es_banco = any(k in medio_lower for k in ("banco", "transferencia", "cheque", "ch", "deposito"))

    codigo_debe = "1102" if es_banco else "1101"
    nombre_debe = "Bancos (Moneda Nacional)" if es_banco else "Caja General"
    codigo_haber = "1103"
    nombre_haber = "Cuentas por Cobrar Clientes"

    glosa_final = glosa or f"Abono de clientes a su cuenta ({'transferencia/banco' if es_banco else 'efectivo'})"

    return crear_partida_simple(
        numero=numero,
        fecha=fecha,
        glosa=glosa_final,
        monto=monto,
        codigo_debe=codigo_debe,
        nombre_debe=nombre_debe,
        codigo_haber=codigo_haber,
        nombre_haber=nombre_haber,
        origen=TipoOrigenPartida.OPERACION,
        documento_soporte=documento_soporte,
    )


def crear_partida_abono_proveedor(
    numero: int,
    fecha: date,
    monto: Decimal,
    medio: str = "banco",  # 'banco' o 'caja'
    glosa: Optional[str] = None,
    documento_soporte: Optional[str] = None,
) -> PartidaDiario:
    """Registra un pago / abono a la cuenta de proveedores."""
    medio_lower = medio.strip().lower()
    es_caja = any(k in medio_lower for k in ("caja", "efectivo"))

    codigo_debe = "2101"
    nombre_debe = "Proveedores Locales"
    codigo_haber = "1101" if es_caja else "1102"
    nombre_haber = "Caja General" if es_caja else "Bancos (Moneda Nacional)"

    glosa_final = glosa or f"Abono a proveedores ({'efectivo' if es_caja else 'cheque/transferencia bancaria'})"

    return crear_partida_simple(
        numero=numero,
        fecha=fecha,
        glosa=glosa_final,
        monto=monto,
        codigo_debe=codigo_debe,
        nombre_debe=nombre_debe,
        codigo_haber=codigo_haber,
        nombre_haber=nombre_haber,
        origen=TipoOrigenPartida.OPERACION,
        documento_soporte=documento_soporte,
    )


def crear_partida_deposito_banco(
    numero: int,
    fecha: date,
    monto: Decimal,
    glosa: Optional[str] = None,
    documento_soporte: Optional[str] = None,
) -> PartidaDiario:
    """Registra un traslado / depósito de fondos desde Caja General hacia el Banco."""
    glosa_final = glosa or "Depósito de efectivo en cuenta bancaria"
    return crear_partida_simple(
        numero=numero,
        fecha=fecha,
        glosa=glosa_final,
        monto=monto,
        codigo_debe="1102",
        nombre_debe="Bancos (Moneda Nacional)",
        codigo_haber="1101",
        nombre_haber="Caja General",
        origen=TipoOrigenPartida.OPERACION,
        documento_soporte=documento_soporte,
    )


def crear_partida_retiro_banco(
    numero: int,
    fecha: date,
    monto: Decimal,
    glosa: Optional[str] = None,
    documento_soporte: Optional[str] = None,
) -> PartidaDiario:
    """Registra un retiro de dinero del Banco para disponibilidad en Caja."""
    glosa_final = glosa or "Retiro de cuenta bancaria para disponibilidad en caja"
    return crear_partida_simple(
        numero=numero,
        fecha=fecha,
        glosa=glosa_final,
        monto=monto,
        codigo_debe="1101",
        nombre_debe="Caja General",
        codigo_haber="1102",
        nombre_haber="Bancos (Moneda Nacional)",
        origen=TipoOrigenPartida.OPERACION,
        documento_soporte=documento_soporte,
    )


def crear_partida_abono_prestamo(
    numero: int,
    fecha: date,
    monto: Decimal,
    codigo_prestamo: str = "2202",
    nombre_prestamo: str = "Préstamos Bancarios a Largo Plazo",
    codigo_pago: str = "1102",
    nombre_pago: str = "Bancos (Moneda Nacional)",
    glosa: Optional[str] = None,
    documento_soporte: Optional[str] = None,
) -> PartidaDiario:
    """Registra un abono o amortización a capital de préstamo bancario."""
    glosa_final = glosa or "Amortización / abono a préstamo bancario por transferencia"
    return crear_partida_simple(
        numero=numero,
        fecha=fecha,
        glosa=glosa_final,
        monto=monto,
        codigo_debe=codigo_prestamo,
        nombre_debe=nombre_prestamo,
        codigo_haber=codigo_pago,
        nombre_haber=nombre_pago,
        origen=TipoOrigenPartida.OPERACION,
        documento_soporte=documento_soporte,
    )
