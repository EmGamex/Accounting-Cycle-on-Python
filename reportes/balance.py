"""Generación del reporte de Balance de Situación General (Apertura y Cierre)."""
from decimal import Decimal
from typing import Any, List

from .exportador import exportar_archivo_texto
from .formato import formato_moneda, linea_doble, linea_simple


def generar_texto_balance(resumen: Any, ancho: int = 75) -> str:
    """Genera la representación formal en texto del Balance de Situación General de Apertura.

    Args:
        resumen: Objeto ResumenBalance con la estructura contable calculada.
        ancho: Ancho total en caracteres de las líneas divisorias.

    Returns:
        Texto formateado del balance general clasificado.
    """
    lineas: List[str] = []
    lineas.append(linea_doble(ancho))
    lineas.append("BALANCE DE SITUACIÓN GENERAL DE APERTURA".center(ancho))
    lineas.append(linea_doble(ancho))

    for clase, subgrupos in resumen.estructura_balance.items():
        lineas.append(f"\n{clase.upper()}")
        total_clase = Decimal("0.00")

        for subgrupo, ctas in subgrupos.items():
            lineas.append(f"  {subgrupo}:")
            subtotal_grupo = Decimal("0.00")

            for cta in ctas.values():
                signo = "(-)" if cta.es_regularizadora else "   "
                etiqueta = f"{signo} [{cta.codigo}] {cta.nombre}"
                lineas.append(f"    {etiqueta:<50} {formato_moneda(cta.monto, ancho=16)}")
                if cta.es_regularizadora:
                    subtotal_grupo -= cta.monto
                else:
                    subtotal_grupo += cta.monto

            etiqueta_subtotal = f"Subtotal {subgrupo}"
            lineas.append(f"    {etiqueta_subtotal:<50} {formato_moneda(subtotal_grupo, ancho=16)}")
            total_clase += subtotal_grupo

        lineas.append(f"  {linea_simple(ancho - 6)}")
        etiqueta_total_clase = f"TOTAL {clase.upper()}"
        lineas.append(f"  {etiqueta_total_clase:<52} {formato_moneda(total_clase, ancho=16)}")

    lineas.append("\n" + linea_doble(ancho))
    lineas.append(f"{'TOTAL ACTIVO:':<54} {formato_moneda(resumen.total_activo, ancho=16)}")
    lineas.append(f"{'TOTAL PASIVO Y PATRIMONIO:':<54} {formato_moneda(resumen.total_pasivo_y_patrimonio, ancho=16)}")
    lineas.append(linea_doble(ancho))

    if resumen.cuadra:
        lineas.append("Estado: CUADRADO EXACTO (Activo = Pasivo + Patrimonio)")
    else:
        dif = abs(resumen.total_activo - resumen.total_pasivo_y_patrimonio)
        lineas.append(f"Estado: DESCUADRADO por {formato_moneda(dif)}")

    return "\n".join(lineas)


def generar_texto_balance_general_cierre(balance_general: Any, ancho: int = 75) -> str:
    """Genera la representación formal en texto del Balance de Situación General de Cierre.

    Args:
        balance_general: Objeto BalanceSituacionGeneral.
        ancho: Ancho total en caracteres.

    Returns:
        Cadena con el reporte contable formateado.
    """
    lineas: List[str] = []
    lineas.append(linea_doble(ancho))
    lineas.append(balance_general.empresa.upper().center(ancho))
    lineas.append(f"BALANCE DE SITUACIÓN GENERAL DE CIERRE - EJERCICIO {balance_general.periodo}".center(ancho))
    lineas.append(f"Cifras en Quetzales (Q) al {balance_general.fecha_emision.strftime('%d/%m/%Y')}".center(ancho))
    lineas.append(linea_doble(ancho))

    # 1. ACTIVO
    lineas.append("\n1. ACTIVO")
    for clase, subgrupos in balance_general.estructura.items():
        if "activo" not in clase.lower():
            continue
        for subgrupo, items in subgrupos.items():
            lineas.append(f"  {subgrupo}:")
            subtotal = Decimal("0.00")
            for item in items:
                signo = "(-)" if item.es_regularizadora else "   "
                etiqueta = f"{signo} [{item.codigo}] {item.nombre}"
                lineas.append(f"    {etiqueta:<50} {formato_moneda(item.monto, ancho=16)}")
                if item.es_regularizadora:
                    subtotal -= item.monto
                else:
                    subtotal += item.monto
            lineas.append(f"    {'Subtotal ' + subgrupo:<50} {formato_moneda(subtotal, ancho=16)}")

    lineas.append(f"  {linea_simple(ancho - 6)}")
    lineas.append(f"  {'TOTAL ACTIVO:':<52} {formato_moneda(balance_general.total_activo, ancho=16)}")

    # 2. PASIVO
    lineas.append("\n2. PASIVO")
    for clase, subgrupos in balance_general.estructura.items():
        if "pasivo" not in clase.lower():
            continue
        for subgrupo, items in subgrupos.items():
            lineas.append(f"  {subgrupo}:")
            subtotal = Decimal("0.00")
            for item in items:
                signo = "(-)" if item.es_regularizadora else "   "
                etiqueta = f"{signo} [{item.codigo}] {item.nombre}"
                lineas.append(f"    {etiqueta:<50} {formato_moneda(item.monto, ancho=16)}")
                subtotal += item.monto
            lineas.append(f"    {'Subtotal ' + subgrupo:<50} {formato_moneda(subtotal, ancho=16)}")

    lineas.append(f"  {linea_simple(ancho - 6)}")
    lineas.append(f"  {'TOTAL PASIVO:':<52} {formato_moneda(balance_general.total_pasivo, ancho=16)}")

    # 3. PATRIMONIO NETO
    lineas.append("\n3. CAPITAL / PATRIMONIO NETO")
    for clase, subgrupos in balance_general.estructura.items():
        if not any(k in clase.lower() for k in ("capital", "patrimonio")):
            continue
        for subgrupo, items in subgrupos.items():
            lineas.append(f"  {subgrupo}:")
            subtotal = Decimal("0.00")
            for item in items:
                signo = "(-)" if item.es_regularizadora else "   "
                etiqueta = f"{signo} [{item.codigo}] {item.nombre}"
                lineas.append(f"    {etiqueta:<50} {formato_moneda(item.monto, ancho=16)}")
                if item.es_regularizadora:
                    subtotal -= item.monto
                else:
                    subtotal += item.monto
            lineas.append(f"    {'Subtotal ' + subgrupo:<50} {formato_moneda(subtotal, ancho=16)}")

    lineas.append(f"  {linea_simple(ancho - 6)}")
    lineas.append(f"  {'TOTAL PATRIMONIO NETO:':<52} {formato_moneda(balance_general.total_patrimonio, ancho=16)}")

    # TOTALES Y CUADRE
    lineas.append("\n" + linea_doble(ancho))
    lineas.append(f"{'TOTAL ACTIVO:':<54} {formato_moneda(balance_general.total_activo, ancho=16)}")
    lineas.append(f"{'TOTAL PASIVO Y PATRIMONIO:':<54} {formato_moneda(balance_general.total_pasivo_y_patrimonio, ancho=16)}")
    lineas.append(linea_doble(ancho))

    if balance_general.cuadra:
        lineas.append("Estado: CUADRADO EXACTO (Activo = Pasivo + Patrimonio)")
    else:
        lineas.append(f"Estado: DESCUADRADO por {formato_moneda(balance_general.diferencia)}")

    return "\n".join(lineas)


def exportar_reporte_apertura(
    resumen: Any,
    partida: Any,
    ruta_archivo: str = "apertura_contable.txt",
) -> str:
    """Exporta el Balance de Situación General y la Partida de Apertura a un archivo de texto."""
    from .partidas import generar_texto_partida

    num = getattr(partida, "numero", 1)
    titulo = f"PARTIDA DE DIARIO NO. {num} (ASIENTO DE APERTURA)"
    texto_pda = "\n" + generar_texto_partida(partida, ancho=75, titulo_personalizado=titulo)
    contenido = generar_texto_balance(resumen) + "\n\n" + texto_pda
    return exportar_archivo_texto(contenido, ruta_archivo)


def exportar_reporte_balance_cierre(
    balance_general: Any,
    ruta_archivo: str = "balance_situacion_general.txt",
) -> str:
    """Exporta el Balance de Situación General de Cierre a un archivo de texto en disco."""
    contenido = generar_texto_balance_general_cierre(balance_general)
    return exportar_archivo_texto(contenido, ruta_archivo)


exportar_reporte = exportar_reporte_apertura
