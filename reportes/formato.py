from config import SIMBOLO_MONEDA
from decimal import Decimal
from typing import Optional


def formato_moneda(monto: Decimal, simbolo: str = SIMBOLO_MONEDA, ancho: Optional[int] = None) -> str:
    """Formatea un monto decimal a la convención oficial guatemalteca (Q #,##0.00).

    Args:
        monto: Importe numérico en Decimal.
        simbolo: Símbolo monetario (por defecto 'Q' para Quetzales).
        ancho: Ancho total opcional para alinear a la derecha.

    Returns:
        Cadena con el monto formateado con separador de miles y dos decimales.
    """
    texto = f"{simbolo} {monto:,.2f}"
    if ancho is not None:
        return f"{texto:>{ancho}}"
    return texto


def linea_simple(ancho: int = 80, char: str = "-") -> str:
    """Genera una línea divisoria simple."""
    return char * ancho


def linea_doble(ancho: int = 80, char: str = "=") -> str:
    """Genera una línea divisoria doble de cierre contable."""
    return char * ancho


def centrar_titulo(texto: str, ancho: int = 80) -> str:
    """Centra un texto dentro del ancho de columna especificado."""
    return texto.center(ancho)
