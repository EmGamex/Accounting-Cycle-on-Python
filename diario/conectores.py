"""Adaptadores y conectores para transformar partidas de apertura y planilla en PartidaDiario."""
from datetime import date
from decimal import Decimal
import re
from typing import Optional, Tuple

from apertura.models import PartidaApertura
from planilla.models import PartidaContable

from .models import MovimientoLinea, PartidaDiario, TipoOrigenPartida


def parse_linea_planilla(texto_cuenta: str) -> Tuple[str, str]:
    """Extrae el código contable y el nombre limpio de una línea generada por el módulo de planilla.

    Ejemplos de entrada:
        '5201-01  Sueldos Administración' -> ('5201-01', 'Sueldos Administración')
        '2104-01  a: Cuotas IGSS por Pagar (Laboral + Patronal)' -> ('2104-01', 'Cuotas IGSS por Pagar (Laboral + Patronal)')
        '1102        Bancos (Pago Líquido de Nómina)' -> ('1102', 'Bancos (Pago Líquido de Nómina)')
    """
    texto_limpio = texto_cuenta.strip()
    partes = texto_limpio.split(maxsplit=1)
    if len(partes) == 1:
        return partes[0], partes[0]

    codigo = partes[0].strip()
    resto = partes[1].strip()

    resto = re.sub(r"^a\s*:\s*", "", resto, flags=re.IGNORECASE).strip()

    return codigo, resto


def de_partida_apertura(
    partida_apertura: PartidaApertura,
    fecha: Optional[date] = None,
    numero: Optional[int] = None,
) -> PartidaDiario:
    """Convierte un objeto PartidaApertura en una PartidaDiario unificada."""
    fecha_partida = fecha or date.today()
    num = numero if numero is not None else partida_apertura.numero

    lineas_diario = []
    # Convención formal guatemalteca: débitos preceden a créditos con sangría legal
    cargos = [l for l in partida_apertura.lineas if l.debe > Decimal("0.00")]
    abonos = [l for l in partida_apertura.lineas if l.haber > Decimal("0.00")]

    for l in cargos + abonos:
        lineas_diario.append(
            MovimientoLinea(
                codigo=l.codigo.strip(),
                nombre=l.nombre.strip(),
                debe=l.debe,
                haber=l.haber,
            )
        )

    return PartidaDiario(
        numero=num,
        fecha=fecha_partida,
        glosa=partida_apertura.descripcion,
        lineas=lineas_diario,
        origen=TipoOrigenPartida.APERTURA,
    )


def de_partida_planilla(
    partida_planilla: PartidaContable,
    fecha: Optional[date] = None,
    numero: int = 2,
    glosa: Optional[str] = None,
) -> PartidaDiario:
    """Convierte un objeto PartidaContable (del módulo planilla) en una PartidaDiario unificada."""
    fecha_partida = fecha or date.today()
    glosa_final = glosa or "Registro de sueldos y salarios del período con retenciones y cuotas patronales de ley."

    lineas_diario = []

    # Procesar cuentas deudoras (Debe)
    for cta_str, monto in partida_planilla.debe:
        codigo, nombre = parse_linea_planilla(cta_str)
        lineas_diario.append(
            MovimientoLinea(
                codigo=codigo,
                nombre=nombre,
                debe=monto,
                haber=Decimal("0.00"),
            )
        )

    # Procesar cuentas acreedoras (Haber)
    for cta_str, monto in partida_planilla.haber:
        codigo, nombre = parse_linea_planilla(cta_str)
        lineas_diario.append(
            MovimientoLinea(
                codigo=codigo,
                nombre=nombre,
                debe=Decimal("0.00"),
                haber=monto,
            )
        )

    return PartidaDiario(
        numero=numero,
        fecha=fecha_partida,
        glosa=glosa_final,
        lineas=lineas_diario,
        origen=TipoOrigenPartida.PLANILLA,
    )
