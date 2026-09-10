"""Generación y formateo de reportes contables: Balance General y Partida de Diario."""
from decimal import Decimal
import os
from typing import Optional

from apertura.models import PartidaApertura, ResumenBalance


def formatear_quetzales(monto: Decimal) -> str:
    """Formatea un importe Decimal a moneda nacional guatemalteca (Q #,##0.00)."""
    return f"Q {monto:>14,.2f}"


def generar_texto_balance(resumen: ResumenBalance) -> str:
    """Genera la representación en texto del Balance de Situación General de Apertura."""
    lineas = []
    lineas.append("=" * 75)
    lineas.append("                    BALANCE DE SITUACIÓN GENERAL DE APERTURA")
    lineas.append("=" * 75)

    for clase, subgrupos in resumen.estructura_balance.items():
        lineas.append(f"\n{clase.upper()}")
        total_clase = Decimal("0.00")

        for subgrupo, ctas in subgrupos.items():
            lineas.append(f"  {subgrupo}:")
            subtotal_grupo = Decimal("0.00")

            for cta in ctas.values():
                signo = "(-)" if cta.es_regularizadora else "   "
                etiqueta = f"{signo} [{cta.codigo}] {cta.nombre}"
                lineas.append(f"    {etiqueta:<50} {formatear_quetzales(cta.monto)}")
                if cta.es_regularizadora:
                    subtotal_grupo -= cta.monto
                else:
                    subtotal_grupo += cta.monto

            etiqueta_subtotal = f"Subtotal {subgrupo}"
            lineas.append(f"    {etiqueta_subtotal:<50} {formatear_quetzales(subtotal_grupo)}")
            total_clase += subtotal_grupo

        lineas.append(f"  {'-' * 69}")
        etiqueta_total_clase = f"TOTAL {clase.upper()}"
        lineas.append(f"  {etiqueta_total_clase:<52} {formatear_quetzales(total_clase)}")

    lineas.append("\n" + "=" * 75)
    lineas.append(f"{'TOTAL ACTIVO:':<54} {formatear_quetzales(resumen.total_activo)}")
    lineas.append(f"{'TOTAL PASIVO Y PATRIMONIO:':<54} {formatear_quetzales(resumen.total_pasivo_y_patrimonio)}")
    lineas.append("=" * 75)

    if resumen.cuadra:
        lineas.append("Estado: CUADRADO EXACTO (Activo = Pasivo + Patrimonio)")
    else:
        dif = abs(resumen.total_activo - resumen.total_pasivo_y_patrimonio)
        lineas.append(f"Estado: DESCUADRADO por Q {dif:,.2f}")

    return "\n".join(lineas)


def generar_texto_partida(partida: PartidaApertura) -> str:
    """Genera la representación en texto del asiento contable de apertura."""
    lineas = []
    lineas.append("\n" + "=" * 75)
    lineas.append(f"           PARTIDA DE DIARIO NO. {partida.numero} (ASIENTO DE APERTURA)")
    lineas.append("=" * 75)
    lineas.append(f"{'CÓDIGO':<8} {'CUENTA':<40} {'DEBE (Q)':>12} {'HABER (Q)':>12}")
    lineas.append("-" * 75)

    for item in partida.lineas:
        if item.debe > Decimal("0.00"):
            lineas.append(f"{item.codigo:<8} {item.nombre:<40} {item.debe:>12,.2f} {'':>12}")
        else:
            lineas.append(f"{item.codigo:<8}   a: {item.nombre:<37} {'':>12} {item.haber:>12,.2f}")

    lineas.append("-" * 75)
    lineas.append(f"{'SUMAS IGUALES:':<49} Q {partida.total_debe:>10,.2f} Q {partida.total_haber:>10,.2f}")
    lineas.append("-" * 75)
    lineas.append(f"Razón: {partida.descripcion}\n")

    return "\n".join(lineas)


def exportar_reporte(
    resumen: ResumenBalance,
    partida: PartidaApertura,
    ruta_archivo: str = "apertura_contable.txt",
) -> str:
    """Exporta el Balance y la Partida de Apertura a un archivo de texto."""
    contenido = generar_texto_balance(resumen) + "\n\n" + generar_texto_partida(partida)
    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(contenido)
    return os.path.abspath(ruta_archivo)
