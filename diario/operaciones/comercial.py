"""Generadores de partidas comerciales (Ventas y Compras) con IVA (12%) y multicanal."""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from ..models import MovimientoLinea, PartidaDiario, TipoOrigenPartida
from .calculos import calcular_desglose_iva, distribuir_canales


def crear_partida_venta(
    numero: int,
    fecha: date,
    glosa: str,
    total_factura: Decimal,
    # Distribución porcentual de cobro
    pct_efectivo: Decimal = Decimal("0.00"),
    pct_banco: Decimal = Decimal("0.00"),
    pct_credito: Decimal = Decimal("0.00"),
    # O montos explícitos
    monto_efectivo: Optional[Decimal] = None,
    monto_banco: Optional[Decimal] = None,
    monto_credito: Optional[Decimal] = None,
    # Cuentas configurables
    codigo_efectivo: str = "1101",
    nombre_efectivo: str = "Caja General",
    codigo_banco: str = "1102",
    nombre_banco: str = "Bancos (Moneda Nacional)",
    codigo_credito: str = "1103",
    nombre_credito: str = "Cuentas por Cobrar Clientes",
    # Ingreso e IVA
    codigo_ingreso: str = "4101",
    nombre_ingreso: str = "Ventas de Mercancías",
    codigo_iva: str = "2105",
    nombre_iva: str = "IVA por Pagar",
    # Compatibilidad retroactiva
    codigo_cobro: Optional[str] = None,
    nombre_cobro: Optional[str] = None,
    documento_soporte: Optional[str] = None,
) -> PartidaDiario:
    """Genera una partida de venta con desglose automático de IVA (12%) y cobro (contado/crédito/bancos)."""
    base, iva = calcular_desglose_iva(total_factura)

    # Definir canales de cobro
    canales = []
    if codigo_cobro:
        # Modo heredado explícito: 100% a la cuenta indicada
        nom_c = nombre_cobro or "Caja General"
        canales.append((codigo_cobro, nom_c, Decimal("1.00"), None))
    else:
        hay_distribucion = (
            pct_efectivo > 0 or pct_banco > 0 or pct_credito > 0 or
            monto_efectivo is not None or monto_banco is not None or monto_credito is not None
        )
        if not hay_distribucion:
            # Por defecto 100% Caja General
            canales.append((codigo_efectivo, nombre_efectivo, Decimal("1.00"), None))
        else:
            canales.append((codigo_efectivo, nombre_efectivo, pct_efectivo, monto_efectivo))
            canales.append((codigo_banco, nombre_banco, pct_banco, monto_banco))
            canales.append((codigo_credito, nombre_credito, pct_credito, monto_credito))

    cobros = distribuir_canales(total_factura, canales)

    lineas: List[MovimientoLinea] = []
    # Cargos al Debe por los canales de cobro
    for cod, nom, monto in cobros:
        lineas.append(MovimientoLinea(codigo=cod, nombre=nom, debe=monto, haber=Decimal("0.00")))

    # Abonos al Haber por Ingreso e IVA Débito Fiscal
    lineas.append(MovimientoLinea(codigo=codigo_ingreso, nombre=nombre_ingreso, debe=Decimal("0.00"), haber=base))
    lineas.append(MovimientoLinea(codigo=codigo_iva, nombre=nombre_iva, debe=Decimal("0.00"), haber=iva))

    return PartidaDiario(
        numero=numero,
        fecha=fecha,
        glosa=glosa,
        lineas=lineas,
        origen=TipoOrigenPartida.VENTA,
        documento_soporte=documento_soporte,
    )


def crear_partida_compra(
    numero: int,
    fecha: date,
    glosa: str,
    total_factura: Decimal,
    codigo_gasto: str = "5201",
    nombre_gasto: str = "Gastos de Administración (Sueldos, Luz, Agua)",
    # Distribución porcentual de pago
    pct_efectivo: Decimal = Decimal("0.00"),
    pct_banco: Decimal = Decimal("0.00"),
    pct_proveedores: Decimal = Decimal("0.00"),
    # O montos explícitos
    monto_efectivo: Optional[Decimal] = None,
    monto_banco: Optional[Decimal] = None,
    monto_proveedores: Optional[Decimal] = None,
    # Cuentas configurables
    codigo_efectivo: str = "1101",
    nombre_efectivo: str = "Caja General",
    codigo_banco: str = "1102",
    nombre_banco: str = "Bancos (Moneda Nacional)",
    codigo_proveedores: str = "2101",
    nombre_proveedores: str = "Proveedores Locales",
    # IVA
    codigo_iva: str = "1107",
    nombre_iva: str = "Crédito Fiscal",
    # Compatibilidad retroactiva
    codigo_pago: Optional[str] = None,
    nombre_pago: Optional[str] = None,
    documento_soporte: Optional[str] = None,
) -> PartidaDiario:
    """Genera una partida de compra o gasto con desglose automático de IVA Crédito Fiscal (12%) y pagos."""
    base, iva = calcular_desglose_iva(total_factura)

    # Definir canales de pago
    canales = []
    if codigo_pago:
        # Modo heredado explícito: 100% a la cuenta indicada
        nom_p = nombre_pago or "Bancos (Moneda Nacional)"
        canales.append((codigo_pago, nom_p, Decimal("1.00"), None))
    else:
        hay_distribucion = (
            pct_efectivo > 0 or pct_banco > 0 or pct_proveedores > 0 or
            monto_efectivo is not None or monto_banco is not None or monto_proveedores is not None
        )
        if not hay_distribucion:
            # Por defecto 100% Bancos
            canales.append((codigo_banco, nombre_banco, Decimal("1.00"), None))
        else:
            canales.append((codigo_efectivo, nombre_efectivo, pct_efectivo, monto_efectivo))
            canales.append((codigo_banco, nombre_banco, pct_banco, monto_banco))
            canales.append((codigo_proveedores, nombre_proveedores, pct_proveedores, monto_proveedores))

    pagos = distribuir_canales(total_factura, canales)

    lineas: List[MovimientoLinea] = []
    # Cargos al Debe por Gasto/Activo y Crédito Fiscal IVA
    lineas.append(MovimientoLinea(codigo=codigo_gasto, nombre=nombre_gasto, debe=base, haber=Decimal("0.00")))
    lineas.append(MovimientoLinea(codigo=codigo_iva, nombre=nombre_iva, debe=iva, haber=Decimal("0.00")))

    # Abonos al Haber por los canales de pago
    for cod, nom, monto in pagos:
        lineas.append(MovimientoLinea(codigo=cod, nombre=nom, debe=Decimal("0.00"), haber=monto))

    return PartidaDiario(
        numero=numero,
        fecha=fecha,
        glosa=glosa,
        lineas=lineas,
        origen=TipoOrigenPartida.COMPRA,
        documento_soporte=documento_soporte,
    )
