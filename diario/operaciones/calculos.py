"""Cálculos y utilidades de prorrateo financiero y fiscal (IVA Guatemala)."""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple

from config import PRECISION_CENTAVOS, TASA_IVA

TWO_PLACES = PRECISION_CENTAVOS
FACTOR_BASE = Decimal("1.00") + TASA_IVA


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
