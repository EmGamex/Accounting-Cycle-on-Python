# -*- coding: utf-8 -*-
"""Componente especializado en la construcción y renderizado de tablas Rich para el sistema contable."""
from decimal import Decimal
from typing import Any, List, Optional, Sequence, Tuple
from rich.table import Table

from config import FORMATO_FECHA, SIMBOLO_MONEDA
from ui.consola import console, formatear_moneda, imprimir_alerta, imprimir_exito
from ui.temas import (
    BORDE_TABLA,
    BORDE_T_GRAFICA,
    COLOR_ATENUADO,
    COLOR_EXITO,
    COLOR_PRIMARIO,
    COLOR_SECUNDARIO,
    COLOR_TEXTO,
)


def generar_tabla_partida(
    partida: Any,
    titulo_personalizado: Optional[str] = None,
) -> Table:
    """Genera una tabla estilizada con Rich para una partida contable a doble columna."""
    fecha_obj = getattr(partida, "fecha", None)
    if titulo_personalizado:
        titulo = titulo_personalizado
    elif fecha_obj and hasattr(fecha_obj, "strftime"):
        titulo = f"Partida No. {partida.numero} ({fecha_obj.strftime(FORMATO_FECHA)})"
    else:
        titulo = f"Partida No. {partida.numero}"

    tabla = Table(title=titulo, box=BORDE_TABLA, expand=False, show_footer=True)
    tabla.add_column("Código", style="dim cyan", no_wrap=True)
    tabla.add_column("Cuenta / Concepto", style=COLOR_TEXTO)
    tabla.add_column(f"Debe ({SIMBOLO_MONEDA})", justify="right", style=COLOR_EXITO, footer_style=COLOR_EXITO, no_wrap=True)
    tabla.add_column(f"Haber ({SIMBOLO_MONEDA})", justify="right", style=COLOR_EXITO, footer_style=COLOR_EXITO, no_wrap=True)

    for linea in partida.lineas:
        es_cargo = getattr(linea, "es_cargo", None)
        if es_cargo is None:
            es_cargo = linea.debe > Decimal("0.00")

        if es_cargo:
            monto_d = formatear_moneda(linea.debe)
            tabla.add_row(str(linea.codigo), linea.nombre, monto_d, "")
        else:
            monto_h = formatear_moneda(linea.haber)
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
    tabla.columns[2].footer = f"[{estilo_pie}]{formatear_moneda(partida.total_debe)}[/{estilo_pie}]"
    tabla.columns[3].footer = f"[{estilo_pie}]{formatear_moneda(partida.total_haber)}[/{estilo_pie}]"

    return tabla


def imprimir_partida_rich(partida: Any, console_obj=None, titulo_personalizado: Optional[str] = None) -> None:
    """Imprime en consola una partida contable con Rich."""
    c = console_obj or console
    tabla = generar_tabla_partida(partida, titulo_personalizado=titulo_personalizado)
    c.print(tabla)


def generar_tabla_sumas_y_saldos(mayor: Any) -> Table:
    """Genera la tabla de sumas y saldos para el resumen de cuentas del Libro Mayor."""
    cuentas = mayor.cuentas_ordenadas

    tabla = Table(title="RESUMEN DE CUENTAS MAYORIZADAS (SUMAS Y SALDOS)", box=BORDE_TABLA, show_footer=True)
    tabla.add_column("Código", style="dim cyan", no_wrap=True)
    tabla.add_column("Cuenta", style=COLOR_TEXTO)
    tabla.add_column("Debe", justify="right", style="green", footer_style="bold green", no_wrap=True)
    tabla.add_column("Haber", justify="right", style="green", footer_style="bold green", no_wrap=True)
    tabla.add_column("S.Deudor", justify="right", style="bold green", footer_style="bold green", no_wrap=True)
    tabla.add_column("S.Acreedor", justify="right", style="bold green", footer_style="bold green", no_wrap=True)

    for c in cuentas:
        d_str = formatear_moneda(c.total_debe)
        h_str = formatear_moneda(c.total_haber)
        sd_str = formatear_moneda(c.saldo_deudor) if c.saldo_deudor > 0 else "-"
        sa_str = formatear_moneda(c.saldo_acreedor) if c.saldo_acreedor > 0 else "-"
        nom_trunc = c.nombre[:26] + ".." if len(c.nombre) > 28 else c.nombre
        tabla.add_row(c.codigo, nom_trunc, d_str, h_str, sd_str, sa_str)

    tot_d = formatear_moneda(mayor.total_debe)
    tot_h = formatear_moneda(mayor.total_haber)
    tot_sd = formatear_moneda(mayor.total_saldos_deudores)
    tot_sa = formatear_moneda(mayor.total_saldos_acreedores)

    tabla.columns[1].footer = "SUMAS:"
    tabla.columns[2].footer = tot_d
    tabla.columns[3].footer = tot_h
    tabla.columns[4].footer = tot_sd
    tabla.columns[5].footer = tot_sa

    return tabla


def generar_tabla_t_grafica(cuenta: Any) -> Table:
    """Genera una tabla Rich estilizada que representa una T-Gráfica contable individual."""
    from itertools import zip_longest
    from mayor.models import NaturalezaSaldo

    titulo = f"[{cuenta.codigo}] {cuenta.nombre}"
    cargos = getattr(cuenta, "cargos", [])
    abonos = getattr(cuenta, "abonos", [])

    tabla = Table(title=titulo, box=BORDE_T_GRAFICA, show_edge=False, show_footer=True)
    tabla.add_column("DEBE (Cargos)", justify="right", style="green", footer_style="bold green")
    tabla.add_column("HABER (Abonos)", justify="right", style="green", footer_style="bold green")

    if not cargos and not abonos:
        tabla.add_row("[dim]Sin movimientos[/dim]", "[dim]Sin movimientos[/dim]")
    else:
        for c, a in zip_longest(cargos, abonos):
            col_c = f"Pda #{c.numero_partida}   {formatear_moneda(c.debe)}" if c is not None else ""
            col_a = f"Pda #{a.numero_partida}   {formatear_moneda(a.haber)}" if a is not None else ""
            tabla.add_row(col_c, col_a)

    tabla.columns[0].footer = f"SUMA: {formatear_moneda(cuenta.total_debe)}"
    tabla.columns[1].footer = f"SUMA: {formatear_moneda(cuenta.total_haber)}"

    tipo = getattr(cuenta, "tipo_saldo", NaturalezaSaldo.SALDADA)
    if tipo == NaturalezaSaldo.SALDADA:
        txt_saldo = f"SALDO: {formatear_moneda(cuenta.saldo)} (CUENTA SALDADA)"
    elif tipo == NaturalezaSaldo.DEUDOR:
        txt_saldo = f"SALDO DEUDOR: {formatear_moneda(cuenta.saldo)}"
    else:
        txt_saldo = f"SALDO ACREEDOR: {formatear_moneda(cuenta.saldo)}"

    if getattr(cuenta, "es_saldo_anomalo", False):
        nat_esperada = getattr(cuenta.naturaleza_esperada, "value", str(cuenta.naturaleza_esperada))
        txt_saldo += f" [bold yellow][ALERTA: Saldo contrario a naturaleza {nat_esperada}][/bold yellow]"

    tabla.caption = txt_saldo
    return tabla


def generar_tabla_mayor_formal(cuenta: Any, folio: int = 1) -> Table:
    """Genera una tabla Rich estilizada a 3 columnas para una cuenta del Libro Mayor."""
    titulo = f"CUENTA: [{cuenta.codigo}] {cuenta.nombre} | FOLIO: {folio:02d}"
    tabla = Table(title=titulo, box=BORDE_TABLA, show_footer=True)
    tabla.add_column("Fecha", style="dim", no_wrap=True)
    tabla.add_column("Pda", justify="center", no_wrap=True)
    tabla.add_column("Concepto / Glosa", style=COLOR_TEXTO)
    tabla.add_column("Debe", justify="right", style="green", footer_style="bold green", no_wrap=True)
    tabla.add_column("Haber", justify="right", style="green", footer_style="bold green", no_wrap=True)
    tabla.add_column("Saldo", justify="right", style="bold green", footer_style="bold green", no_wrap=True)

    movimientos = cuenta.calcular_movimientos_con_saldo() if hasattr(cuenta, "calcular_movimientos_con_saldo") else []
    if not movimientos:
        tabla.add_row("", "", "[dim]Sin movimientos registrados[/dim]", "", "", "")
    else:
        for m in movimientos:
            fecha_str = m.fecha.strftime(FORMATO_FECHA) if hasattr(m.fecha, "strftime") else str(m.fecha)
            pda_str = str(m.numero_partida)
            concepto = m.concepto
            debe_str = formatear_moneda(m.debe) if m.debe > Decimal("0.00") else ""
            haber_str = formatear_moneda(m.haber) if m.haber > Decimal("0.00") else ""
            saldo_str = formatear_moneda(m.saldo_acumulado)
            tabla.add_row(fecha_str, pda_str, concepto, debe_str, haber_str, saldo_str)

    tipo_saldo_nombre = getattr(cuenta.tipo_saldo, "value", str(cuenta.tipo_saldo)).capitalize()
    tabla.columns[2].footer = f"SUMAS Y SALDO FINAL [{tipo_saldo_nombre}]:"
    tabla.columns[3].footer = formatear_moneda(cuenta.total_debe)
    tabla.columns[4].footer = formatear_moneda(cuenta.total_haber)
    tabla.columns[5].footer = formatear_moneda(cuenta.saldo)

    return tabla


def generar_tabla_cuentas_registradas(cuentas: Sequence[Any]) -> Table:
    """Genera la tabla de cuentas iniciales registradas en el flujo de Apertura."""
    tabla = Table(title="Cuentas Registradas Actualmente", box=BORDE_TABLA)
    tabla.add_column("Código", style="dim cyan", no_wrap=True)
    tabla.add_column("Nombre", style=COLOR_TEXTO)
    tabla.add_column("Tipo", style="yellow")
    tabla.add_column("Monto (Q)", justify="right", style=COLOR_EXITO, no_wrap=True)

    for cta in cuentas:
        tipo = "(-)" if getattr(cta, "es_regularizadora", False) else "Normal"
        tabla.add_row(cta.codigo, cta.nombre, tipo, formatear_moneda(cta.monto))

    return tabla


def generar_tabla_boleta(r: Any) -> Table:
    """Genera la tabla individual de boleta de pago para un empleado."""
    titulo = f"BOLETA DE PAGO: {r.empleado.upper()} ({r.departamento})"
    tabla = Table(title=titulo, box=BORDE_TABLA)
    tabla.add_column("Concepto", style=COLOR_TEXTO)
    tabla.add_column("Monto (Q)", justify="right", style=COLOR_EXITO, no_wrap=True)

    filas: List[Tuple[str, Decimal, bool]] = [
        ("Sueldo Base Ordinario", r.sueldo_base, True),
        ("Comisiones sobre Ventas", r.comisiones, r.comisiones > Decimal("0.00")),
        (f"Sueldo Extra ({r.horas_extras_trabajadas}h)", r.sueldo_extraordinario, r.sueldo_extraordinario > Decimal("0.00")),
        ("Bonificación Incentivo", r.bonificacion_ley, True),
        ("TOTAL DEVENGADO", r.total_devengado, True),
        ("Cuota Laboral IGSS (4.83%)", r.descuento_igss, True),
        ("Retención ISR", r.descuento_isr, r.descuento_isr > Decimal("0.00")),
        ("Anticipo sobre Sueldos", r.prestamos_deudas, r.prestamos_deudas > Decimal("0.00")),
        ("Deudores Empleados / Otros", r.otros_descuentos, r.otros_descuentos > Decimal("0.00")),
        ("TOTAL DESCUENTOS", r.total_descuentos, True),
        ("LÍQUIDO A RECIBIR", r.liquido_recibir, True),
    ]

    for etiqueta, monto, mostrar in filas:
        if mostrar:
            estilo = "bold cyan" if "TOTAL" in etiqueta or "LÍQUIDO" in etiqueta else "white"
            tabla.add_row(f"[{estilo}]{etiqueta}[/{estilo}]", formatear_moneda(monto))

    return tabla


def generar_tabla_partida_nomina(p: Any) -> Table:
    """Genera la tabla del asiento contable en partida doble para sueldos y salarios."""
    tabla = Table(title="PARTIDA CONTABLE DE SUELDOS Y SALARIOS", box=BORDE_TABLA, show_footer=True)
    tabla.add_column("Código / Cuenta", style=COLOR_TEXTO)
    tabla.add_column("Debe (Q)", justify="right", style="green", footer_style="bold green", no_wrap=True)
    tabla.add_column("Haber (Q)", justify="right", style="green", footer_style="bold green", no_wrap=True)

    for cuenta, monto in p.debe:
        if monto > Decimal("0.00"):
            tabla.add_row(cuenta, formatear_moneda(monto), "")

    for cuenta, monto in p.haber:
        if monto > Decimal("0.00"):
            tabla.add_row(f"  a: {cuenta}", "", formatear_moneda(monto))

    tabla.columns[0].footer = "SUMAS IGUALES"
    tabla.columns[1].footer = formatear_moneda(p.total_debe)
    tabla.columns[2].footer = formatear_moneda(p.total_haber)

    return tabla


def generar_tabla_balance_4_columnas(balance_4c: Any) -> Table:
    """Genera una tabla Rich estilizada para el Balance de Comprobación y Saldos (4 Columnas)."""
    titulo = f"BALANCE DE COMPROBACIÓN Y SALDOS (4 COLUMNAS) - EJERCICIO {getattr(balance_4c, 'periodo', '2026')}"
    tabla = Table(title=titulo, box=BORDE_TABLA, show_footer=True)
    tabla.add_column("No.", justify="right", style="dim", no_wrap=True)
    tabla.add_column("Código", style="dim cyan", no_wrap=True)
    tabla.add_column("Cuenta", style=COLOR_TEXTO)
    tabla.add_column("Suma Debe", justify="right", style="green", footer_style="bold green", no_wrap=True)
    tabla.add_column("Suma Haber", justify="right", style="green", footer_style="bold green", no_wrap=True)
    tabla.add_column("Saldo Deudor", justify="right", style="bold green", footer_style="bold green", no_wrap=True)
    tabla.add_column("Saldo Acreedor", justify="right", style="bold green", footer_style="bold green", no_wrap=True)

    for f in getattr(balance_4c, "filas", []):
        nom = f.nombre[:30] + ".." if len(f.nombre) > 32 else f.nombre
        if getattr(f, "es_saldo_anomalo", False):
            nom += " [bold yellow]*[/bold yellow]"
        sd_str = formatear_moneda(f.saldo_deudor) if f.saldo_deudor > Decimal("0.00") else "-"
        sa_str = formatear_moneda(f.saldo_acreedor) if f.saldo_acreedor > Decimal("0.00") else "-"
        tabla.add_row(
            str(f.numero),
            f.codigo,
            nom,
            formatear_moneda(f.suma_debe),
            formatear_moneda(f.suma_haber),
            sd_str,
            sa_str,
        )

    cuadra = getattr(balance_4c, "cuadra", False)
    estilo_pie = "bold green" if cuadra else "bold red"

    tabla.columns[2].footer = f"[{estilo_pie}]SUMAS IGUALES:[/{estilo_pie}]"
    tabla.columns[3].footer = f"[{estilo_pie}]{formatear_moneda(balance_4c.total_debe)}[/{estilo_pie}]"
    tabla.columns[4].footer = f"[{estilo_pie}]{formatear_moneda(balance_4c.total_haber)}[/{estilo_pie}]"
    tabla.columns[5].footer = f"[{estilo_pie}]{formatear_moneda(balance_4c.total_saldos_deudores)}[/{estilo_pie}]"
    tabla.columns[6].footer = f"[{estilo_pie}]{formatear_moneda(balance_4c.total_saldos_acreedores)}[/{estilo_pie}]"

    return tabla


def generar_tabla_balance_general(balance_general: Any) -> Table:
    """Genera una tabla Rich clasificada para el Balance de Situación General de Cierre."""
    titulo = f"BALANCE DE SITUACIÓN GENERAL DE CIERRE - EJERCICIO {getattr(balance_general, 'periodo', '2026')}"
    tabla = Table(title=titulo, box=BORDE_TABLA, show_footer=True)
    tabla.add_column("Clasificación / Cuenta", style=COLOR_TEXTO)
    tabla.add_column("Código", style="dim cyan", no_wrap=True)
    tabla.add_column("Monto Parcial (Q)", justify="right", style="green", no_wrap=True)
    tabla.add_column("Total Rubro (Q)", justify="right", style="bold green", footer_style="bold green", no_wrap=True)

    # 1. ACTIVO
    tabla.add_row("[bold cyan]1. ACTIVO[/bold cyan]", "", "", "")
    for clase, subgrupos in getattr(balance_general, "estructura", {}).items():
        if "activo" not in clase.lower():
            continue
        for subgrupo, items in subgrupos.items():
            tabla.add_row(f"  [bold]{subgrupo}[/bold]", "", "", "")
            subtot = Decimal("0.00")
            for item in items:
                signo = "(-)" if item.es_regularizadora else "   "
                tabla.add_row(f"    {signo} {item.nombre}", item.codigo, formatear_moneda(item.monto), "")
                if item.es_regularizadora:
                    subtot -= item.monto
                else:
                    subtot += item.monto
            tabla.add_row(f"    [italic]Subtotal {subgrupo}[/italic]", "", "", formatear_moneda(subtot))

    tabla.add_row("[bold green]TOTAL ACTIVO[/bold green]", "", "", f"[bold green]{formatear_moneda(balance_general.total_activo)}[/bold green]")
    tabla.add_row("", "", "", "")

    # 2. PASIVO
    tabla.add_row("[bold cyan]2. PASIVO[/bold cyan]", "", "", "")
    for clase, subgrupos in getattr(balance_general, "estructura", {}).items():
        if "pasivo" not in clase.lower():
            continue
        for subgrupo, items in subgrupos.items():
            tabla.add_row(f"  [bold]{subgrupo}[/bold]", "", "", "")
            subtot = Decimal("0.00")
            for item in items:
                signo = "(-)" if item.es_regularizadora else "   "
                tabla.add_row(f"    {signo} {item.nombre}", item.codigo, formatear_moneda(item.monto), "")
                subtot += item.monto
            tabla.add_row(f"    [italic]Subtotal {subgrupo}[/italic]", "", "", formatear_moneda(subtot))

    tabla.add_row("[bold green]TOTAL PASIVO[/bold green]", "", "", f"[bold green]{formatear_moneda(balance_general.total_pasivo)}[/bold green]")
    tabla.add_row("", "", "", "")

    # 3. PATRIMONIO NETO
    tabla.add_row("[bold cyan]3. CAPITAL / PATRIMONIO NETO[/bold cyan]", "", "", "")
    for clase, subgrupos in getattr(balance_general, "estructura", {}).items():
        if not any(k in clase.lower() for k in ("capital", "patrimonio")):
            continue
        for subgrupo, items in subgrupos.items():
            tabla.add_row(f"  [bold]{subgrupo}[/bold]", "", "", "")
            subtot = Decimal("0.00")
            for item in items:
                signo = "(-)" if item.es_regularizadora else "   "
                tabla.add_row(f"    {signo} {item.nombre}", item.codigo, formatear_moneda(item.monto), "")
                if item.es_regularizadora:
                    subtot -= item.monto
                else:
                    subtot += item.monto
            tabla.add_row(f"    [italic]Subtotal {subgrupo}[/italic]", "", "", formatear_moneda(subtot))

    tabla.add_row("[bold green]TOTAL PATRIMONIO NETO[/bold green]", "", "", f"[bold green]{formatear_moneda(balance_general.total_patrimonio)}[/bold green]")

    cuadra = getattr(balance_general, "cuadra", False)
    estilo_pie = "bold green" if cuadra else "bold red"
    tabla.columns[0].footer = f"[{estilo_pie}]TOTAL PASIVO Y PATRIMONIO NETO:[/{estilo_pie}]"
    tabla.columns[3].footer = f"[{estilo_pie}]{formatear_moneda(balance_general.total_pasivo_y_patrimonio)}[/{estilo_pie}]"

    return tabla


def generar_tabla_estado_resultados(resumen: Any) -> Table:
    """Genera una tabla Rich con el Estado de Resultados condensado."""
    tabla = Table(title="ESTADO DE RESULTADOS CONDENSADO (PÉRDIDAS Y GANANCIAS)", box=BORDE_TABLA)
    tabla.add_column("Concepto", style=COLOR_TEXTO)
    tabla.add_column("Monto (Q)", justify="right", style="bold green", no_wrap=True)

    tabla.add_row("Ingresos Operacionales y Extraordinarios", formatear_moneda(resumen.total_ingresos))
    tabla.add_row("(-) Costos de Ventas y Compras", f"({formatear_moneda(resumen.total_costos)})")
    tabla.add_row("(-) Gastos de Operación y Financieros", f"({formatear_moneda(resumen.total_gastos)})")

    estilo = "bold green" if resumen.es_ganancia else "bold red"
    etiqueta = "GANANCIA NETA DEL EJERCICIO" if resumen.es_ganancia else "PÉRDIDA NETA DEL EJERCICIO"
    tabla.add_row(f"[{estilo}]{etiqueta}[/{estilo}]", f"[{estilo}]{formatear_moneda(abs(resumen.resultado_ejercicio))}[/{estilo}]")

    return tabla

