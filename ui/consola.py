# -*- coding: utf-8 -*-
"""Instancia global de consola y funciones utilitarias de presentación y entrada."""
from decimal import Decimal
from typing import Optional, Sequence, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from config import SIMBOLO_MONEDA
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
        console.print(f"  [{COLOR_INDICE}][{idx}][/{COLOR_INDICE}] {desc}")
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
