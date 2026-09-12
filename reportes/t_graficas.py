"""Módulo de renderizado de T-Gráficas contables en texto plano / ASCII."""
from itertools import zip_longest
from typing import List, Optional

from mayor.models import CuentaMayor, LibroMayor, NaturalezaSaldo
from .formato import centrar_titulo, formato_moneda, linea_doble, linea_simple


def generar_texto_t_grafica(cuenta: CuentaMayor, ancho_col: int = 26) -> str:
    """Genera la representación visual de una T-Gráfica contable para una cuenta individual.

    Estructura de la T:
      - Encabezado: [Código] Nombre
      - Columna Izquierda: DEBE (Cargos) con 'Pda #N  Q monto'
      - Columna Derecha: HABER (Abonos) con 'Pda #N  Q monto'
      - Línea divisoria y pie con sumas totales
      - Determinación de Saldo (Deudor / Acreedor / Saldada)

    Args:
        cuenta: Instancia de CuentaMayor con sus movimientos.
        ancho_col: Ancho en caracteres de cada columna (brazo de la T).

    Returns:
        Cadena formateada con la T-Gráfica completa.
    """
    lineas: List[str] = []
    ancho_total = (ancho_col * 2) + 1

    # Título centrado sobre la T
    titulo = f"[{cuenta.codigo}] {cuenta.nombre}"
    lineas.append(centrar_titulo(titulo, ancho_total))

    # Encabezado de columnas
    tit_debe = "DEBE (Cargos)".center(ancho_col)
    tit_haber = "HABER (Abonos)".center(ancho_col)
    lineas.append(f"{tit_debe}│{tit_haber}")

    # Barra superior de la T
    barra_horizontal = ("─" * ancho_col) + "┼" + ("─" * ancho_col)
    lineas.append(barra_horizontal)

    # Detalle de movimientos emparejados fila a fila
    cargos = cuenta.cargos
    abonos = cuenta.abonos

    if not cargos and not abonos:
        vacio_debe = "Sin movimientos".center(ancho_col)
        vacio_haber = "Sin movimientos".center(ancho_col)
        lineas.append(f"{vacio_debe}│{vacio_haber}")
    else:
        for c, a in zip_longest(cargos, abonos):
            # Formato Debe
            if c is not None:
                ref_c = f"Pda #{c.numero_partida:<3}"
                monto_c = formato_moneda(c.debe)
                # Espaciado interno: ref_c a la izquierda, monto_c a la derecha
                espacio_c = ancho_col - len(ref_c) - len(monto_c) - 2
                col_c = f" {ref_c}{' ' * max(0, espacio_c)}{monto_c} "
            else:
                col_c = " " * ancho_col

            # Formato Haber
            if a is not None:
                ref_a = f"Pda #{a.numero_partida:<3}"
                monto_a = formato_moneda(a.haber)
                espacio_a = ancho_col - len(ref_a) - len(monto_a) - 2
                col_a = f" {ref_a}{' ' * max(0, espacio_a)}{monto_a} "
            else:
                col_a = " " * ancho_col

            lineas.append(f"{col_c}│{col_a}")

    # Línea de cierre de movimientos
    lineas.append(barra_horizontal)

    # Sumas al pie de la T
    lbl_debe = "SUMA:"
    monto_tot_d = formato_moneda(cuenta.total_debe)
    esp_d = ancho_col - len(lbl_debe) - len(monto_tot_d) - 2
    pie_debe = f" {lbl_debe}{' ' * max(0, esp_d)}{monto_tot_d} "

    lbl_haber = "SUMA:"
    monto_tot_h = formato_moneda(cuenta.total_haber)
    esp_h = ancho_col - len(lbl_haber) - len(monto_tot_h) - 2
    pie_haber = f" {lbl_haber}{' ' * max(0, esp_h)}{monto_tot_h} "

    lineas.append(f"{pie_debe}│{pie_haber}")

    # Base de la T
    base_t = ("═" * ancho_col) + "┴" + ("═" * ancho_col)
    lineas.append(base_t)

    # Determinación y visualización del Saldo
    if cuenta.tipo_saldo == NaturalezaSaldo.SALDADA:
        txt_saldo = f"SALDO: {formato_moneda(cuenta.saldo)} (CUENTA SALDADA)"
    elif cuenta.tipo_saldo == NaturalezaSaldo.DEUDOR:
        txt_saldo = f"SALDO DEUDOR: {formato_moneda(cuenta.saldo)}"
    else:
        txt_saldo = f"SALDO ACREEDOR: {formato_moneda(cuenta.saldo)}"

    if cuenta.es_saldo_anomalo:
        txt_saldo += f" [ALERTA: Saldo contrario a naturaleza {cuenta.naturaleza_esperada.value}]"

    lineas.append(centrar_titulo(txt_saldo, ancho_total))
    return "\n".join(lineas)


def generar_texto_todas_t_graficas(
    libro_mayor: LibroMayor,
    empresa: str = "EMPRESA GUATEMALTECA, S.A.",
    ancho_col: int = 26,
) -> str:
    """Genera el reporte consolidado con todas las T-Gráficas del ejercicio."""
    bloques: List[str] = []
    ancho_total = max(72, (ancho_col * 2) + 1)

    bloques.append(linea_doble(ancho_total))
    bloques.append(centrar_titulo(empresa, ancho_total))
    bloques.append(centrar_titulo("LIBRO MAYOR - REPORTE DE T-GRÁFICAS", ancho_total))
    bloques.append(centrar_titulo("(Cifras expresadas en Quetzales - Q)", ancho_total))
    bloques.append(linea_doble(ancho_total))
    bloques.append("")

    cuentas = libro_mayor.cuentas_ordenadas
    if not cuentas:
        bloques.append(centrar_titulo("No hay movimientos registrados en el Libro Mayor.", ancho_total))
        return "\n".join(bloques)

    for c in cuentas:
        bloques.append(generar_texto_t_grafica(c, ancho_col=ancho_col))
        bloques.append("")
        bloques.append(linea_simple(ancho_total, char="·"))
        bloques.append("")

    # Resumen y comprobación al final
    bloques.append(linea_doble(ancho_total))
    bloques.append(centrar_titulo("RESUMEN DE SUMAS Y SALDOS DEL MAYOR", ancho_total))
    bloques.append(linea_doble(ancho_total))
    bloques.append(f"Total de Cuentas con Movimiento: {len(cuentas)}")
    bloques.append(f"Suma Total Debe Mayor:           {formato_moneda(libro_mayor.total_debe):>20}")
    bloques.append(f"Suma Total Haber Mayor:          {formato_moneda(libro_mayor.total_haber):>20}")
    bloques.append(f"Suma Total Saldos Deudores:      {formato_moneda(libro_mayor.total_saldos_deudores):>20}")
    bloques.append(f"Suma Total Saldos Acreedores:    {formato_moneda(libro_mayor.total_saldos_acreedores):>20}")
    estado = "CUADRE EXACTO" if libro_mayor.cuadra else f"DESCUADRADO (Dif: Q{libro_mayor.diferencia_sumas})"
    bloques.append(f"Estado de Cuadre:                {estado:>20}")
    bloques.append(linea_doble(ancho_total))

    return "\n".join(bloques)


def exportar_reporte_t_graficas(
    libro_mayor: LibroMayor,
    ruta_archivo: str = "t_graficas_mayor.txt",
    empresa: str = "EMPRESA GUATEMALTECA, S.A.",
) -> str:
    """Exporta el reporte de T-Gráficas a un archivo de texto en disco."""
    from .exportador import exportar_archivo_texto
    contenido = generar_texto_todas_t_graficas(libro_mayor, empresa=empresa)
    return exportar_archivo_texto(contenido, ruta_archivo)
