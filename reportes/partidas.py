"""Renderizador universal de asientos contables (partidas de diario) en texto plano."""
from datetime import date
from decimal import Decimal
from typing import Any, List, Optional, Protocol, Sequence

from .formato import formato_moneda, linea_doble, linea_simple


class LineaContableProtocol(Protocol):
    codigo: str
    nombre: str
    debe: Decimal
    haber: Decimal


class PartidaContableProtocol(Protocol):
    numero: int
    lineas: Sequence[LineaContableProtocol]
    total_debe: Decimal
    total_haber: Decimal


def generar_texto_partida(
    partida: Any,
    ancho: int = 80,
    titulo_personalizado: Optional[str] = None,
) -> str:
    """Genera la representación en texto formal de una partida contable en partida doble.

    Compatible tanto con PartidaDiario como con PartidaApertura u otros asientos contables.

    Args:
        partida: Objeto partida que contiene número, líneas, sumas y glosa/descripción.
        ancho: Ancho en caracteres del reporte (por defecto 80).
        titulo_personalizado: Título opcional que reemplaza el encabezado estándar.

    Returns:
        Cadena formateada lista para impresión o guardado.
    """
    lineas_salida: List[str] = []

    # Encabezado
    lineas_salida.append(linea_simple(ancho))
    fecha_obj: Optional[date] = getattr(partida, "fecha", None)

    if titulo_personalizado:
        lineas_salida.append(titulo_personalizado.center(ancho))
    elif fecha_obj and hasattr(fecha_obj, "strftime"):
        titulo = f" PARTIDA No. {partida.numero} "
        fecha_str = f" Fecha: {fecha_obj.strftime('%d/%m/%Y')} "
        mitad = ancho // 2
        lineas_salida.append(f"{titulo:<{mitad}}{fecha_str:>{ancho - mitad}}")
    else:
        titulo = f" PARTIDA DE DIARIO NO. {partida.numero} "
        lineas_salida.append(titulo.center(ancho))

    lineas_salida.append(linea_simple(ancho))
    lineas_salida.append(f"{'CODIGO':<9} {'CUENTA / CONCEPTO':<43} {'DEBE':>12} {'HABER':>14}")
    lineas_salida.append(linea_simple(ancho))

    # Detalle de líneas (Cargos primero, luego Abonos con sangría legal "a: ")
    for linea in partida.lineas:
        es_cargo = getattr(linea, "es_cargo", None)
        if es_cargo is None:
            es_cargo = linea.debe > Decimal("0.00")

        if es_cargo:
            monto_debe = formato_moneda(linea.debe)
            lineas_salida.append(f"{linea.codigo:<9} {linea.nombre:<43} {monto_debe:>12} {'':>14}")
        else:
            monto_haber = formato_moneda(linea.haber)
            nombre_abono = f"a: {linea.nombre}"
            lineas_salida.append(f"{linea.codigo:<9}   {nombre_abono:<41} {'':>12} {monto_haber:>14}")

    # Glosa explicativa / Razón
    lineas_salida.append("")
    glosa = getattr(partida, "glosa", None) or getattr(partida, "descripcion", "")
    glosa_txt = f"    ( {glosa} )"
    doc_soporte = getattr(partida, "documento_soporte", None)
    if doc_soporte:
        glosa_txt += f" [Doc: {doc_soporte}]"
    lineas_salida.append(glosa_txt)

    # Líneas de cuadre y sumas iguales
    lineas_salida.append(f"{'':<53} {'-'*12} {'-'*14}")
    total_d = formato_moneda(partida.total_debe)
    total_h = formato_moneda(partida.total_haber)
    lineas_salida.append(f"{'':<35} {'SUMAS IGUALES:':<17} {total_d:>12} {total_h:>14}")
    lineas_salida.append(f"{'':<53} {'='*12} {'='*14}")

    return "\n".join(lineas_salida)


def generar_tabla_partida_rich(
    partida: Any,
    titulo_personalizado: Optional[str] = None,
):
    """Genera una tabla estilizada con Rich para una partida contable a doble columna."""
    from rich import box
    from rich.table import Table

    fecha_obj = getattr(partida, "fecha", None)
    if titulo_personalizado:
        titulo = titulo_personalizado
    elif fecha_obj and hasattr(fecha_obj, "strftime"):
        titulo = f"Partida No. {partida.numero} ({fecha_obj.strftime('%d/%m/%Y')})"
    else:
        titulo = f"Partida No. {partida.numero}"

    tabla = Table(title=titulo, box=box.ROUNDED, expand=False, show_footer=True)
    tabla.add_column("Código", style="dim cyan", no_wrap=True)
    tabla.add_column("Cuenta / Concepto", style="white")
    tabla.add_column("Debe (Q)", justify="right", style="bold green", footer_style="bold green", no_wrap=True)
    tabla.add_column("Haber (Q)", justify="right", style="bold green", footer_style="bold green", no_wrap=True)

    for linea in partida.lineas:
        es_cargo = getattr(linea, "es_cargo", None)
        if es_cargo is None:
            es_cargo = linea.debe > Decimal("0.00")

        if es_cargo:
            monto_d = f"Q{linea.debe:,.2f}"
            tabla.add_row(str(linea.codigo), linea.nombre, monto_d, "")
        else:
            monto_h = f"Q{linea.haber:,.2f}"
            tabla.add_row(str(linea.codigo), f"  a: {linea.nombre}", "", monto_h)

    glosa = getattr(partida, "glosa", None) or getattr(partida, "descripcion", "")
    doc_soporte = getattr(partida, "documento_soporte", None)
    glosa_txt = f"[dim italic]{glosa}[/dim italic]"
    if doc_soporte:
        glosa_txt += f" [dim][Doc: {doc_soporte}][/dim]"

    tabla.add_row("", glosa_txt, "", "")

    cuadra = partida.total_debe == partida.total_haber
    estilo_pie = "bold green" if cuadra else "bold red"
    tabla.columns[1].footer = f"[{estilo_pie}]SUMAS IGUALES[/{estilo_pie}]"
    tabla.columns[2].footer = f"[{estilo_pie}]Q{partida.total_debe:,.2f}[/{estilo_pie}]"
    tabla.columns[3].footer = f"[{estilo_pie}]Q{partida.total_haber:,.2f}[/{estilo_pie}]"

    return tabla


def imprimir_partida_rich(partida: Any, console_obj=None, titulo_personalizado: Optional[str] = None) -> None:
    """Imprime en consola una partida contable con Rich."""
    try:
        from ui import console
        c = console_obj or console
        tabla = generar_tabla_partida_rich(partida, titulo_personalizado=titulo_personalizado)
        c.print(tabla)
    except ImportError:
        print(generar_texto_partida(partida, titulo_personalizado=titulo_personalizado))
