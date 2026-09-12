"""Generación del reporte de Balance de Situación General de Apertura."""
from decimal import Decimal
from typing import Any, List

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


def exportar_reporte_apertura(
    resumen: Any,
    partida: Any,
    ruta_archivo: str = "apertura_contable.txt",
) -> str:
    """Exporta el Balance de Situación General y la Partida de Apertura a un archivo de texto.

    Args:
        resumen: Objeto ResumenBalance calculado.
        partida: Objeto de partida contable de apertura.
        ruta_archivo: Ruta de destino del archivo.

    Returns:
        Ruta absoluta del archivo generado.
    """
    from .exportador import exportar_archivo_texto
    from .partidas import generar_texto_partida

    num = getattr(partida, "numero", 1)
    titulo = f"PARTIDA DE DIARIO NO. {num} (ASIENTO DE APERTURA)"
    texto_pda = "\n" + generar_texto_partida(partida, ancho=75, titulo_personalizado=titulo)
    contenido = generar_texto_balance(resumen) + "\n\n" + texto_pda
    return exportar_archivo_texto(contenido, ruta_archivo)


exportar_reporte = exportar_reporte_apertura

