"""Módulo de reporte del Libro Mayor formal a 3 columnas."""
from typing import List

from mayor.models import CuentaMayor, LibroMayor, NaturalezaSaldo
from .formato import centrar_titulo, formato_moneda, linea_doble, linea_simple


def generar_texto_mayor_cuenta(cuenta: CuentaMayor, folio: int = 1, ancho: int = 85) -> str:
    """Genera la representación formal a 3 columnas de una cuenta individual del Mayor."""
    lineas: List[str] = []

    lineas.append(linea_doble(ancho))
    izq = f" CUENTA: [{cuenta.codigo}] {cuenta.nombre}"
    der = f"FOLIO: {folio:02d} "
    espacio = ancho - len(izq) - len(der)
    lineas.append(f"{izq}{' ' * max(0, espacio)}{der}")
    lineas.append(linea_doble(ancho))

    lineas.append(f"{'FECHA':<10} {'PDA':<5} {'CONCEPTO / GLOSA':<28} {'DEBE':>13} {'HABER':>13} {'SALDO':>14}")
    lineas.append(linea_simple(ancho))

    movimientos = cuenta.calcular_movimientos_con_saldo()
    if not movimientos:
        lineas.append(centrar_titulo("Sin movimientos registrados", ancho))
    else:
        for m in movimientos:
            fecha_str = m.fecha.strftime("%d/%m/%Y")
            pda_str = str(m.numero_partida)
            concepto_trunc = m.concepto[:26] + ".." if len(m.concepto) > 28 else m.concepto
            debe_str = formato_moneda(m.debe) if m.debe > 0 else ""
            haber_str = formato_moneda(m.haber) if m.haber > 0 else ""
            saldo_str = formato_moneda(m.saldo_acumulado)

            lineas.append(
                f"{fecha_str:<10} {pda_str:<5} {concepto_trunc:<28} "
                f"{debe_str:>13} {haber_str:>13} {saldo_str:>14}"
            )

    lineas.append(linea_simple(ancho))
    tot_d = formato_moneda(cuenta.total_debe)
    tot_h = formato_moneda(cuenta.total_haber)
    tot_s = formato_moneda(cuenta.saldo)
    tipo_s = f"[{cuenta.tipo_saldo.value.capitalize()}]"

    lineas.append(
        f"{'SUMAS Y SALDO FINAL:':<44} {tot_d:>13} {tot_h:>13} {tot_s:>14}"
    )
    lineas.append(f"{'':<44} {'=' * 13} {'=' * 13} {'=' * 14}")
    lineas.append(f"{'ESTADO DEL SALDO:':<44} {tipo_s:>42}")
    lineas.append(linea_doble(ancho))

    return "\n".join(lineas)


def generar_texto_libro_mayor_formal(
    libro_mayor: LibroMayor,
    empresa: str = "EMPRESA GUATEMALTECA, S.A.",
    ancho: int = 85,
) -> str:
    """Genera el Libro Mayor formal completo a 3 columnas para todas las cuentas."""
    bloques: List[str] = []

    bloques.append(linea_doble(ancho))
    bloques.append(centrar_titulo(empresa, ancho))
    bloques.append(centrar_titulo("LIBRO MAYOR DE OPERACIONES (A 3 COLUMNAS)", ancho))
    bloques.append(centrar_titulo("(Cifras expresadas en Quetzales - Q)", ancho))
    bloques.append(linea_doble(ancho))
    bloques.append("")

    cuentas = libro_mayor.cuentas_ordenadas
    if not cuentas:
        bloques.append(centrar_titulo("No hay movimientos registrados en el Libro Mayor.", ancho))
        return "\n".join(bloques)

    for folio, c in enumerate(cuentas, start=1):
        bloques.append(generar_texto_mayor_cuenta(c, folio=folio, ancho=ancho))
        bloques.append("")

    bloques.append(linea_doble(ancho))
    bloques.append(centrar_titulo("RESUMEN GENERAL DEL LIBRO MAYOR", ancho))
    bloques.append(linea_doble(ancho))
    bloques.append(f"Total de Cuentas / Folios:       {len(cuentas)}")
    bloques.append(f"Suma Total Debe:                 {formato_moneda(libro_mayor.total_debe):>20}")
    bloques.append(f"Suma Total Haber:                {formato_moneda(libro_mayor.total_haber):>20}")
    bloques.append(f"Suma Total Saldos Deudores:      {formato_moneda(libro_mayor.total_saldos_deudores):>20}")
    bloques.append(f"Suma Total Saldos Acreedores:    {formato_moneda(libro_mayor.total_saldos_acreedores):>20}")
    estado = "CUADRE EXACTO" if libro_mayor.cuadra else f"DESCUADRADO (Dif: Q{libro_mayor.diferencia_sumas})"
    bloques.append(f"Estado de Cuadre del Mayor:      {estado:>20}")
    bloques.append(linea_doble(ancho))

    return "\n".join(bloques)


def exportar_reporte_libro_mayor(
    libro_mayor: LibroMayor,
    ruta_archivo: str = "libro_mayor_formal.txt",
    empresa: str = "EMPRESA GUATEMALTECA, S.A.",
) -> str:
    """Exporta el reporte del Libro Mayor a un archivo de texto en disco."""
    from .exportador import exportar_archivo_texto
    contenido = generar_texto_libro_mayor_formal(libro_mayor, empresa=empresa)
    return exportar_archivo_texto(contenido, ruta_archivo)
