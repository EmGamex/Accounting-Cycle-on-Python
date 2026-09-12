# -*- coding: utf-8 -*-
"""Componente especializado en la construcción y renderizado de tablas Rich para el sistema contable."""
from decimal import Decimal
from typing import Any, List, Optional, Sequence, Tuple
from rich.table import Table

from ui.consola import console, formatear_moneda, imprimir_alerta, imprimir_exito
from ui.temas import (
    BORDE_TABLA,
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
        titulo = f"Partida No. {partida.numero} ({fecha_obj.strftime('%d/%m/%Y')})"
    else:
        titulo = f"Partida No. {partida.numero}"

    tabla = Table(title=titulo, box=BORDE_TABLA, expand=False, show_footer=True)
    tabla.add_column("Código", style="dim cyan", no_wrap=True)
    tabla.add_column("Cuenta / Concepto", style=COLOR_TEXTO)
    tabla.add_column("Debe (Q)", justify="right", style=COLOR_EXITO, footer_style=COLOR_EXITO, no_wrap=True)
    tabla.add_column("Haber (Q)", justify="right", style=COLOR_EXITO, footer_style=COLOR_EXITO, no_wrap=True)

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
