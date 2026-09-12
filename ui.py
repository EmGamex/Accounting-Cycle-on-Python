# -*- coding: utf-8 -*-
"""Modulo centralizado de presentacion en terminal con Rich y adaptacion para Termux."""
import os
from decimal import Decimal
from typing import Any, Callable, List, Optional, Sequence, Tuple
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Consola unificada para toda la aplicacion
console = Console()


def obtener_ancho_consola(min_ancho: int = 40, max_ancho: int = 80) -> int:
    """Retorna un ancho seguro adaptado al terminal actual (especialmente en moviles con Termux)."""
    ancho = console.width
    return max(min_ancho, min(ancho, max_ancho))


def formatear_moneda(monto: Decimal) -> str:
    """Formatea una cantidad monetaria con el simbolo oficial Q y separadores."""
    return f"Q{monto:,.2f}"


def imprimir_banner(titulo: str, subtitulo: Optional[str] = None, border_style: str = "cyan") -> None:
    """Imprime un banner estilizado con bordes redondeados adaptado al ancho de pantalla."""
    texto = Text(titulo, style="bold cyan", justify="center")
    if subtitulo:
        texto.append("\n" + subtitulo, style="dim white")
    console.print(Panel(texto, border_style=border_style, box=box.ROUNDED, expand=True))


def imprimir_estado_ejercicio(
    total_partidas: int, total_debe: Decimal, total_haber: Decimal, cuadra: bool
) -> None:
    """Muestra el estado financiero del ejercicio con badge cromatico dinamico."""
    estado = Text()
    estado.append("Estado del Ejercicio: ", style="bold")
    estado.append(f"{total_partidas} partida(s) en Diario", style="cyan")
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
        console.print(f"  [bold cyan][{idx}][/bold cyan] {desc}")
    console.print(f"  [bold dim][{salir_codigo}][/bold dim] {texto_salir}")


def imprimir_exito(mensaje: str) -> None:
    """Muestra un mensaje de exito con icono verde."""
    console.print(f"  [bold green][OK][/bold green] {mensaje}")


def imprimir_alerta(mensaje: str) -> None:
    """Muestra un mensaje de advertencia o error."""
    console.print(f"  [bold yellow](!)[/bold yellow] {mensaje}")


def imprimir_aviso(mensaje: str) -> None:
    """Muestra un aviso informativo o retorno de flujo."""
    console.print(f"  [bold cyan][!][/bold cyan] {mensaje}")
