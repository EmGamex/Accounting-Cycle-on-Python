# -*- coding: utf-8 -*-
"""Definición centralizada de estilos visuales, paleta de colores y bordes para Rich."""
from rich import box

# Bordes estándar para tablas y paneles (amigables y nítidos en Termux y escritorio)
BORDE_TABLA = box.ROUNDED
BORDE_PANEL = box.ROUNDED
BORDE_COMPACTO = box.SIMPLE

# Paleta de colores semántica
COLOR_PRIMARIO = "bold cyan"
COLOR_SECUNDARIO = "cyan"
COLOR_EXITO = "bold green"
COLOR_ERROR = "bold red"
COLOR_AVISO = "bold yellow"
COLOR_TEXTO = "white"
COLOR_ATENUADO = "dim white"
COLOR_INDICE = "bold cyan"
COLOR_SALIR = "bold dim"

# Badges de estado contable
BADGE_CUADRADO = "[bold green][CUADRADO][/bold green]"
BADGE_DESCUADRADO = "[bold red][DESCUADRADO][/bold red]"
