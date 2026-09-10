"""Generadores de partidas contables para operaciones comerciales frecuentes."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple

from .models import MovimientoLinea, PartidaDiario, TipoOrigenPartida

TWO_PLACES = Decimal("0.01")
TASA_IVA = Decimal("0.12")
FACTOR_BASE = Decimal("1.12")


def normalizar_porcentaje(valor: Decimal | float | int | str) -> Decimal:
    """Normaliza porcentajes expresados en 0-1 (ej. 0.60) o en base 100 (ej. 60)."""
    if not isinstance(valor, Decimal):
        valor = Decimal(str(valor))
    if valor > Decimal("1.00"):
        return (valor / Decimal("100.00")).quantize(Decimal("0.0001"))
    return valor.quantize(Decimal("0.0001"))


def calcular_desglose_iva(total_bruto: Decimal) -> Tuple[Decimal, Decimal]:
    """Calcula base imponible y el IVA (12%) garantizando cuadre exacto al centavo."""
    if not isinstance(total_bruto, Decimal):
        total_bruto = Decimal(str(total_bruto))

    total = total_bruto.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    base = (total / FACTOR_BASE).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    iva = (total - base).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    return base, iva


def distribuir_canales(
    total: Decimal,
    canales: List[Tuple[str, str, Decimal, Optional[Decimal]]],
) -> List[Tuple[str, str, Decimal]]:
    """Distribuye un monto total entre múltiples canales (cuentas) por porcentaje o monto fijo.

    Cada tupla de entrada es: (codigo, nombre, porcentaje, monto_fijo).
    Garantiza reconciliación de centavos para que la suma sea exactamente igual al total.
    """
    if not isinstance(total, Decimal):
        total = Decimal(str(total))
    total = total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    # Filtrar canales activos
    canales_activos = []
    for cod, nom, pct, monto in canales:
        pct_norm = normalizar_porcentaje(pct) if pct else Decimal("0.00")
        if monto is not None or pct_norm > Decimal("0.00"):
            canales_activos.append((cod, nom, pct_norm, monto))

    if not canales_activos:
        return []

    resultados: List[Tuple[str, str, Decimal]] = []
    suma_asignada = Decimal("0.00")

    # Primero asignar los montos fijos
    canales_con_pct = []
    for cod, nom, pct, monto in canales_activos:
        if monto is not None:
            m_val = Decimal(str(monto)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            resultados.append((cod, nom, m_val))
            suma_asignada += m_val
        else:
            canales_con_pct.append((cod, nom, pct))

    # Si hay canales por porcentaje, distribuir el remanente (o el total)
    if canales_con_pct:
        base_a_distribuir = total - suma_asignada
        suma_porcentajes = sum((pct for _, _, pct in canales_con_pct), Decimal("0.00"))

        if suma_porcentajes <= Decimal("0.00"):
            suma_porcentajes = Decimal("1.00")

        asignados_pct = []
        for cod, nom, pct in canales_con_pct:
            # Proporcional sobre el remanente
            fraccion = pct / suma_porcentajes
            monto_calculado = (base_a_distribuir * fraccion).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            asignados_pct.append((cod, nom, monto_calculado))

        # Reconciliar centavos huérfanos por redondeo
        total_pct = sum((m for _, _, m in asignados_pct), Decimal("0.00"))
        diferencia = base_a_distribuir - total_pct

        if diferencia != Decimal("0.00") and asignados_pct:
            # Ajustar la diferencia al último canal activo
            u_cod, u_nom, u_monto = asignados_pct[-1]
            asignados_pct[-1] = (u_cod, u_nom, u_monto + diferencia)

        resultados.extend(asignados_pct)

    return [(cod, nom, m) for cod, nom, m in resultados if m > Decimal("0.00")]


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
