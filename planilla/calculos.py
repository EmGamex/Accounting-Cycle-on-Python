"""Motor de cálculo financiero de nómina y retenciones de ley."""
from decimal import Decimal
from typing import Optional

from .config import (
    BONIFICACION_LEY,
    DEDUCCION_ISR_PERSONAL,
    DIAS_MES_COMERCIAL,
    IGSS_LABORAL,
    IMPORTE_FIJO_ISR_7,
    RECARGO_HORA_EXTRA,
    TASA_ISR_5,
    TASA_ISR_7,
    TRAMO_ISR_5_MAX,
    money,
)
from .models import DatosEmpleado, ResultadoPlanilla


def calcular_isr_mensual(sueldo_base: Decimal) -> Decimal:
    """Calcula la proyección mensual de retención del ISR asalariados (Decreto 10-2012)."""
    sueldo_base = money(sueldo_base)
    renta_neta_anual = sueldo_base * Decimal("12")
    descuento_igss_anual = (sueldo_base * IGSS_LABORAL) * Decimal("12")
    total_deducciones = DEDUCCION_ISR_PERSONAL + descuento_igss_anual
    renta_imponible = renta_neta_anual - total_deducciones

    if renta_imponible <= Decimal("0.00"):
        return Decimal("0.00")

    if renta_imponible <= TRAMO_ISR_5_MAX:
        isr_anual = renta_imponible * TASA_ISR_5
    else:
        isr_anual = IMPORTE_FIJO_ISR_7 + ((renta_imponible - TRAMO_ISR_5_MAX) * TASA_ISR_7)

    return money(isr_anual / Decimal("12"))


def calcular_boleta(
    datos: DatosEmpleado,
    bonificacion_ley: Decimal = BONIFICACION_LEY,
    porcentaje_igss: Decimal = IGSS_LABORAL,
) -> ResultadoPlanilla:
    """Calcula los rubros devengados, descuentos y líquido a recibir con redondeo exacto."""
    sueldo_base = money(datos.sueldo_base)
    comisiones = money(datos.ventas * (datos.pct_comision / Decimal("100.00")))

    jornada = datos.jornada_horas if datos.jornada_horas > Decimal("0") else Decimal("8.0")
    valor_hora_extra = (sueldo_base / DIAS_MES_COMERCIAL / jornada) * RECARGO_HORA_EXTRA
    sueldo_extraordinario = money(datos.horas_extras * valor_hora_extra)

    total_afecto_igss = money(sueldo_base + comisiones + sueldo_extraordinario)
    total_devengado = money(total_afecto_igss + bonificacion_ley)

    descuento_igss = money(total_afecto_igss * porcentaje_igss)
    descuento_isr = (
        money(datos.isr_manual)
        if datos.isr_manual is not None
        else calcular_isr_mensual(sueldo_base)
    )

    prestamos = money(datos.prestamos_deudas)
    otros_desc = money(datos.otros_descuentos)
    total_descuentos = money(descuento_igss + descuento_isr + prestamos + otros_desc)
    liquido_recibir = money(total_devengado - total_descuentos)

    return ResultadoPlanilla(
        empleado=datos.nombre,
        departamento=datos.departamento.strip() or "Administración",
        sueldo_base=sueldo_base,
        comisiones=comisiones,
        horas_extras_trabajadas=datos.horas_extras,
        sueldo_extraordinario=sueldo_extraordinario,
        bonificacion_ley=bonificacion_ley,
        total_afecto_igss=total_afecto_igss,
        total_devengado=total_devengado,
        descuento_igss=descuento_igss,
        descuento_isr=descuento_isr,
        prestamos_deudas=prestamos,
        otros_descuentos=otros_desc,
        total_descuentos=total_descuentos,
        liquido_recibir=liquido_recibir,
    )
