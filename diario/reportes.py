"""Generador de reportes de texto y formateo de partidas para consola."""
from decimal import Decimal
from typing import List

from .models import LibroDiario, MovimientoLinea, PartidaDiario


def formato_moneda(monto: Decimal) -> str:
    """Formatea un monto decimal a la convención oficial guatemalteca (Q #,##0.00)."""
    return f"Q {monto:,.2f}"


def generar_texto_partida(partida: PartidaDiario, ancho: int = 80) -> str:
    """Genera la representación en texto de una partida individual con sangría legal."""
    lineas_salida: List[str] = []

    # Encabezado de la partida
    titulo = f" PARTIDA No. {partida.numero} "
    fecha_str = f" Fecha: {partida.fecha.strftime('%d/%m/%Y')} "
    lineas_salida.append("-" * ancho)
    lineas_salida.append(f"{titulo:<40}{fecha_str:>40}")
    lineas_salida.append("-" * ancho)
    lineas_salida.append(f"{'CODIGO':<9} {'CUENTA / CONCEPTO':<43} {'DEBE':>12} {'HABER':>14}")
    lineas_salida.append("-" * ancho)

    # Detalle de líneas (Cargos primero, luego Abonos con sangría)
    for linea in partida.lineas:
        if linea.es_cargo:
            monto_debe = formato_moneda(linea.debe)
            lineas_salida.append(f"{linea.codigo:<9} {linea.nombre:<43} {monto_debe:>12} {'':>14}")
        else:
            monto_haber = formato_moneda(linea.haber)
            nombre_abono = f"a: {linea.nombre}"
            lineas_salida.append(f"{linea.codigo:<9}   {nombre_abono:<41} {'':>12} {monto_haber:>14}")

    # Glosa explicativa
    lineas_salida.append("")
    glosa_txt = f"    ( {partida.glosa} )"
    if partida.documento_soporte:
        glosa_txt += f" [Doc: {partida.documento_soporte}]"
    lineas_salida.append(glosa_txt)

    # Líneas de cuadre y sumas iguales
    lineas_salida.append(f"{'':<53} {'-'*12} {'-'*14}")
    total_d = formato_moneda(partida.total_debe)
    total_h = formato_moneda(partida.total_haber)
    lineas_salida.append(f"{'':<35} {'SUMAS IGUALES:':<17} {total_d:>12} {total_h:>14}")
    lineas_salida.append(f"{'':<53} {'='*12} {'='*14}")

    return "\n".join(lineas_salida)


def generar_texto_libro_diario(libro: LibroDiario, empresa: str = "EMPRESA GUATEMALTECA, S.A.", ancho: int = 80) -> str:
    """Genera el texto completo del Libro Diario con todas sus partidas y cierre."""
    bloques: List[str] = []

    # Encabezado formal del libro
    bloques.append("=" * ancho)
    bloques.append(f"{empresa.center(ancho)}")
    bloques.append("LIBRO DIARIO DE OPERACIONES".center(ancho))
    bloques.append("(Cifras expresadas en Quetzales - Q)".center(ancho))
    bloques.append("=" * ancho)
    bloques.append("")

    if not libro.partidas:
        bloques.append("No hay partidas registradas en el Libro Diario.".center(ancho))
        return "\n".join(bloques)

    for p in libro.partidas:
        bloques.append(generar_texto_partida(p, ancho=ancho))
        bloques.append("")

    # Resumen y cierre del Libro Diario
    bloques.append("=" * ancho)
    bloques.append("RESUMEN GENERAL DEL LIBRO DIARIO".center(ancho))
    bloques.append("=" * ancho)
    bloques.append(f"Total de Partidas Registradas: {len(libro.partidas)}")
    total_d = formato_moneda(libro.total_debe)
    total_h = formato_moneda(libro.total_haber)
    bloques.append(f"Suma Total Acumulada Debe:    {total_d:>20}")
    bloques.append(f"Suma Total Acumulada Haber:   {total_h:>20}")
    bloques.append(f"Estado de Cuadre:             {'CUADRE EXACTO' if libro.cuadra else 'DESCUADRADO':>20}")
    bloques.append("=" * ancho)

    return "\n".join(bloques)
