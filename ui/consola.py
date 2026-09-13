# -*- coding: utf-8 -*-
"""Instancia global de consola y funciones utilitarias de presentación y entrada."""
from decimal import Decimal
from typing import Any, Optional, Sequence, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from config import RESPUESTAS_AFIRMATIVAS, SIMBOLO_MONEDA
from ui.temas import (
    BORDE_PANEL,
    COLOR_ATENUADO,
    COLOR_AVISO,
    COLOR_ERROR,
    COLOR_EXITO,
    COLOR_INDICE,
    COLOR_PRIMARIO,
    COLOR_SALIR,
    COLOR_SECUNDARIO,
)

# Consola única para toda la aplicación
console = Console()


def obtener_ancho_consola(min_ancho: int = 40, max_ancho: int = 80) -> int:
    """Retorna un ancho seguro adaptado al terminal actual (especialmente en móviles con Termux)."""
    ancho = console.width
    return max(min_ancho, min(ancho, max_ancho))


def pedir_confirmacion(mensaje: str, default: bool = True) -> bool:
    """Solicita confirmación afirmativa o negativa al usuario de forma centralizada."""
    sufijo = " [s]: " if default else " [n]: "
    resp = input(f"\n{mensaje} (s/n){sufijo}").strip().lower()
    if default:
        return resp in RESPUESTAS_AFIRMATIVAS
    return resp in ("s", "si", "y", "yes")


def formatear_moneda(monto: Decimal) -> str:
    """Formatea una cantidad monetaria con el símbolo oficial y separadores de miles."""
    return f"{SIMBOLO_MONEDA}{monto:,.2f}"


def imprimir_banner(titulo: str, subtitulo: Optional[str] = None, border_style: str = "cyan") -> None:
    """Imprime un banner estilizado con bordes redondeados adaptado al ancho de pantalla."""
    texto = Text(titulo, style=COLOR_PRIMARIO, justify="center")
    if subtitulo:
        texto.append("\n" + subtitulo, style=COLOR_ATENUADO)
    console.print(Panel(texto, border_style=border_style, box=BORDE_PANEL, expand=True))


def imprimir_estado_ejercicio(
    total_partidas: int, total_debe: Decimal, total_haber: Decimal, cuadra: bool
) -> None:
    """Muestra el estado financiero del ejercicio con badge cromático dinámico."""
    estado = Text()
    estado.append("Estado del Ejercicio: ", style="bold")
    estado.append(f"{total_partidas} partida(s) en Diario", style=COLOR_SECUNDARIO)
    estado.append(" | Debe: ", style="bold")
    estado.append(formatear_moneda(total_debe), style="green" if cuadra else "yellow")
    estado.append(" | Haber: ", style="bold")
    estado.append(formatear_moneda(total_haber), style="green" if cuadra else "yellow")

    if cuadra:
        estado.append(" [")
        estado.append("CUADRADO", style="bold green")
        estado.append("]")
    else:
        estado.append(" [")
        estado.append("DESCUADRADO", style="bold red")
        estado.append("]")

    console.print(estado)


def imprimir_menu_opciones(
    opciones: Sequence[Tuple[str, str]], texto_salir: str = "Salir", salir_codigo: str = "0"
) -> None:
    """Imprime una lista de opciones estilizadas numeradas con etiquetas de color."""
    for idx, (etiqueta, desc) in enumerate(opciones, start=1):
        codigo = etiqueta if etiqueta else str(idx)
        console.print(f"  [{COLOR_INDICE}][{codigo}][/{COLOR_INDICE}] {desc}")
    console.print(f"  [{COLOR_SALIR}][{salir_codigo}][/{COLOR_SALIR}] {texto_salir}")


def imprimir_exito(mensaje: str) -> None:
    """Muestra un mensaje de éxito con icono verde."""
    console.print(f"  [{COLOR_EXITO}][OK][/{COLOR_EXITO}] {mensaje}")


def imprimir_alerta(mensaje: str) -> None:
    """Muestra un mensaje de advertencia o error."""
    console.print(f"  [{COLOR_AVISO}](!)[/{COLOR_AVISO}] {mensaje}")


def imprimir_aviso(mensaje: str) -> None:
    """Muestra un aviso informativo o retorno de flujo."""
    console.print(f"  [{COLOR_SECUNDARIO}][!][/{COLOR_SECUNDARIO}] {mensaje}")


def imprimir_menu_clasificacion(nombre_cuenta: str) -> None:
    """Muestra el diálogo y opciones disponibles para clasificar una cuenta desconocida."""
    console.print(f"\n  [{COLOR_AVISO}][!][/{COLOR_AVISO}] '{nombre_cuenta}' no se encontró en el catálogo.")
    console.print("  [bold]Clasifícala:[/bold]")
    console.print("  [cyan]1[/cyan]. Activo Corriente     | [cyan]2[/cyan]. Activo No Corriente")
    console.print("  [cyan]3[/cyan]. Pasivo Corriente    | [cyan]4[/cyan]. Pasivo No Corriente")
    console.print("  [cyan]5[/cyan]. Capital / Patrimonio")


def imprimir_coincidencias_cuentas(coincidencias: Sequence[Any], limite: int = 8) -> None:
    """Muestra la lista numerada de coincidencias de catálogo encontradas."""
    console.print(f"\n  Coincidencias encontradas ([bold cyan]{len(coincidencias)}[/bold cyan]):")
    for idx, c in enumerate(coincidencias[:limite], 1):
        es_reg = getattr(c, "es_regularizadora", False)
        tag_reg = " [yellow](-)[/yellow]" if es_reg else "    "
        console.print(f"    [[bold cyan]{idx}[/bold cyan]] [cyan]{c.codigo:<9}[/cyan]{tag_reg} {c.nombre}")


def imprimir_cuenta_seleccionada(cuenta: Any) -> None:
    """Muestra la cuenta que fue seleccionada de forma explícita."""
    es_reg = getattr(cuenta, "es_regularizadora", False)
    tag_reg = " [bold yellow](Cuenta Regularizadora)[/bold yellow]" if es_reg else ""
    console.print(f"  [green]->[/green] Seleccionada: [[cyan]{cuenta.codigo}[/cyan]] {cuenta.nombre}{tag_reg}")


def imprimir_resumen_balance_apertura(resumen: Any) -> None:
    """Muestra el resumen de totales de Activo, Pasivo y Patrimonio con sus colores semánticos."""
    console.rule(style=COLOR_SECUNDARIO)
    console.print(
        f"  Activo Neto: [bold green]{formatear_moneda(resumen.total_activo)}[/bold green] | "
        f"Pasivo: [bold yellow]{formatear_moneda(resumen.total_pasivo)}[/bold yellow] | "
        f"Patrimonio: [bold cyan]{formatear_moneda(resumen.total_patrimonio)}[/bold cyan]"
    )