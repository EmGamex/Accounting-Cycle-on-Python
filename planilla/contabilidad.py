"""Módulo de contabilidad y generación de partida doble de nómina."""
from collections import defaultdict
from decimal import Decimal
from typing import List, Tuple

from .config import IGSS_PATRONAL, money
from .models import PartidaContable, ResultadoPlanilla


def generar_partida_contable(
    lista_planillas: List[ResultadoPlanilla],
    pct_patronal: Decimal = IGSS_PATRONAL,
    separar_departamentos: bool = True,
) -> PartidaContable:
    """Genera el asiento contable consolidado asegurando cuadre perfecto al centavo."""
    if not lista_planillas:
        return PartidaContable()

    debe_cuentas: List[Tuple[str, Decimal]] = []
    haber_cuentas: List[Tuple[str, Decimal]] = []

    # Identificar si hay múltiples departamentos
    deptos = set(p.departamento for p in lista_planillas)
    usar_deptos = separar_departamentos and (len(deptos) > 1 or "Administración" in deptos)

    cuota_patronal_total = Decimal("0.00")

    if usar_deptos:
        # Agrupar por departamento para cuentas de gasto específicas
        por_depto = defaultdict(list)
        for p in lista_planillas:
            por_depto[p.departamento].append(p)

        for depto, empleados in sorted(por_depto.items()):
            sueldo_b = money(sum(e.sueldo_base for e in empleados))
            bonif = money(sum(e.bonificacion_ley for e in empleados))
            comis = money(sum(e.comisiones for e in empleados))
            extra = money(sum(e.sueldo_extraordinario for e in empleados))
            afecto = money(sum(e.total_afecto_igss for e in empleados))
            patronal_depto = money(afecto * pct_patronal)
            cuota_patronal_total += patronal_depto

            es_ventas = "ventas" in depto.lower()
            cod_sueldo = "5202-01" if es_ventas else "5201-01"
            cod_bonif = "5202-02" if es_ventas else "5201-02"
            cod_comis = "5202-03" if es_ventas else "5201-01"
            cod_extra = "5202-05" if es_ventas else "5201-04"
            cod_patronal = "5202-04" if es_ventas else "5201-03"

            debe_cuentas.append((f"{cod_sueldo:<8} Sueldos {depto}", sueldo_b))
            if bonif > Decimal("0.00"):
                debe_cuentas.append((f"{cod_bonif:<8} Bonificación Incentivo {depto}", bonif))
            if comis > Decimal("0.00"):
                debe_cuentas.append((f"{cod_comis:<8} Comisiones sobre Ventas ({depto})", comis))
            if extra > Decimal("0.00"):
                debe_cuentas.append((f"{cod_extra:<8} Sueldos Extraordinarios {depto}", extra))
            if patronal_depto > Decimal("0.00"):
                debe_cuentas.append((f"{cod_patronal:<8} Cuota Patronal {depto}", patronal_depto))
    else:
        # Partida general sin desglose departamental
        sueldo_b = money(sum(p.sueldo_base for p in lista_planillas))
        bonif = money(sum(p.bonificacion_ley for p in lista_planillas))
        comis = money(sum(p.comisiones for p in lista_planillas))
        extra = money(sum(p.sueldo_extraordinario for p in lista_planillas))
        afecto = money(sum(p.total_afecto_igss for p in lista_planillas))
        cuota_patronal_total = money(afecto * pct_patronal)

        debe_cuentas.append(("5201-01  Sueldos Base", sueldo_b))
        if bonif > Decimal("0.00"):
            debe_cuentas.append(("5201-02  Bonificaciones Incentivo", bonif))
        if comis > Decimal("0.00"):
            debe_cuentas.append(("5202-03  Comisiones sobre Ventas", comis))
        if extra > Decimal("0.00"):
            debe_cuentas.append(("5201-04  Sueldos Extraordinarios", extra))
        if cuota_patronal_total > Decimal("0.00"):
            debe_cuentas.append((f"5201-03  Cuotas Patronales ({pct_patronal * 100:.2f}%)", cuota_patronal_total))

    # Cuentas del Haber (Obligaciones y Pagos)
    total_igss_laboral = money(sum(p.descuento_igss for p in lista_planillas))
    igss_por_pagar = money(cuota_patronal_total + total_igss_laboral)
    total_isr = money(sum(p.descuento_isr for p in lista_planillas))
    total_prestamos = money(sum(p.prestamos_deudas for p in lista_planillas))
    total_otros_desc = money(sum(p.otros_descuentos for p in lista_planillas))
    total_liquido = money(sum(p.liquido_recibir for p in lista_planillas))

    if igss_por_pagar > Decimal("0.00"):
        haber_cuentas.append(("2104-01  a: Cuotas IGSS por Pagar (Laboral + Patronal)", igss_por_pagar))
    if total_isr > Decimal("0.00"):
        haber_cuentas.append(("2104-02     Retención ISR por Pagar", total_isr))
    if total_prestamos > Decimal("0.00"):
        haber_cuentas.append(("1111        Anticipos sobre Sueldos", total_prestamos))
    if total_otros_desc > Decimal("0.00"):
        haber_cuentas.append(("1103        Deudores Empleados / Otros Descuentos", total_otros_desc))
    if total_liquido > Decimal("0.00"):
        haber_cuentas.append(("1102        Bancos (Pago Líquido de Nómina)", total_liquido))

    debe_total = money(sum(monto for _, monto in debe_cuentas))
    haber_total = money(sum(monto for _, monto in haber_cuentas))
    diferencia = money(debe_total - haber_total)
    cuadra = (diferencia == Decimal("0.00"))

    return PartidaContable(
        debe=debe_cuentas,
        haber=haber_cuentas,
        total_debe=debe_total,
        total_haber=haber_total,
        cuadra=cuadra,
        diferencia=diferencia,
    )
