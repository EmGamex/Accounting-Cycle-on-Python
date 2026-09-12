"""Generación y exportación de reportes formales en texto plano del Balance de 4 Columnas."""
from decimal import Decimal
from typing import Optional

from balance.models import Balance4Columnas
from reportes.exportador import exportar_archivo_texto
from reportes.formato import centrar_titulo, formato_moneda, linea_doble, linea_simple


def generar_texto_balance_4_columnas(balance_4c: Balance4Columnas, ancho: int = 95) -> str:
    """Genera la representación formal en texto del Balance de Comprobación y Saldos (4 Columnas).

    Estructura legal guatemalteca:
    No. | Código | Cuenta | Suma Debe | Suma Haber | Saldo Deudor | Saldo Acreedor
    """
    lineas = []
    lineas.append(linea_doble(ancho))
    lineas.append(centrar_titulo(balance_4c.empresa.upper(), ancho))
    lineas.append(centrar_titulo(f"BALANCE DE COMPROBACIÓN Y SALDOS (4 COLUMNAS) - EJERCICIO {balance_4c.periodo}", ancho))
    lineas.append(centrar_titulo(f"Cifras expresadas en Quetzales (Q) al {balance_4c.fecha_emision.strftime('%d/%m/%Y')}", ancho))
    lineas.append(linea_doble(ancho))

    encabezado = (
        f"{'No.':<4} {'Código':<8} {'Nombre de la Cuenta':<33} "
        f"{'Suma Debe':>11} {'Suma Haber':>11} {'S. Deudor':>11} {'S. Acreedor':>11}"
    )
    lineas.append(encabezado)
    lineas.append(linea_simple(ancho))

    for f in balance_4c.filas:
        nom_recortado = f.nombre[:31] + ".." if len(f.nombre) > 33 else f.nombre
        sd_str = formato_moneda(f.saldo_deudor, ancho=11) if f.saldo_deudor > Decimal("0.00") else f"{'-':>11}"
        sa_str = formato_moneda(f.saldo_acreedor, ancho=11) if f.saldo_acreedor > Decimal("0.00") else f"{'-':>11}"
        d_str = formato_moneda(f.suma_debe, ancho=11)
        h_str = formato_moneda(f.suma_haber, ancho=11)

        linea_cta = (
            f"{f.numero:<4} {f.codigo:<8} {nom_recortado:<33} "
            f"{d_str} {h_str} {sd_str} {sa_str}"
        )
        lineas.append(linea_cta)

    lineas.append(linea_simple(ancho))

    tot_d = formato_moneda(balance_4c.total_debe, ancho=11)
    tot_h = formato_moneda(balance_4c.total_haber, ancho=11)
    tot_sd = formato_moneda(balance_4c.total_saldos_deudores, ancho=11)
    tot_sa = formato_moneda(balance_4c.total_saldos_acreedores, ancho=11)

    lineas.append(
        f"{'':<4} {'':<8} {'SUMAS IGUALES:':<33} {tot_d} {tot_h} {tot_sd} {tot_sa}"
    )
    lineas.append(linea_doble(ancho))

    if balance_4c.cuadra:
        lineas.append("Estado de Verificación: CUADRADO EXACTO (Sumas Iguales y Saldos Iguales)")
    else:
        lineas.append(
            f"Estado de Verificación: DESCUADRADO "
            f"[Dif. Sumas: {formato_moneda(balance_4c.diferencia_sumas)}, "
            f"Dif. Saldos: {formato_moneda(balance_4c.diferencia_saldos)}]"
        )

    return "\n".join(lineas)


def exportar_reporte_balance_4_columnas(
    balance_4c: Balance4Columnas,
    ruta_archivo: str = "balance_4_columnas.txt",
) -> str:
    """Exporta el reporte del Balance de 4 Columnas a un archivo de texto seguro en UTF-8."""
    contenido = generar_texto_balance_4_columnas(balance_4c)
    return exportar_archivo_texto(contenido, ruta_archivo)
