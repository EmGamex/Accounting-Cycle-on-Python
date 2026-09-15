"""Funciones utilitarias seguras para parseo y extracción de datos."""
from datetime import date
from typing import Any, Dict, Optional

from .exceptions import FormatoArchivoInvalidoError


def extraer_str(data: Dict[str, Any], clave: str, default: str = "") -> str:
    """Extrae un string de forma segura evitando convertir None en 'None'."""
    val = data.get(clave)
    return str(val) if val is not None else default


def extraer_fecha(data: Dict[str, Any], clave: str) -> Optional[date]:
    """Parsea una fecha en formato ISO garantizando el tipo de excepción de dominio."""
    val = data.get(clave)
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val))
    except (ValueError, TypeError) as exc:
        raise FormatoArchivoInvalidoError(
            f"El campo '{clave}' contiene una fecha ISO inválida: '{val}'"
        ) from exc


def extraer_bool(data: Dict[str, Any], clave: str, default: bool = False) -> bool:
    """Extrae un valor booleano manejando cadenas 'true'/'false' y booleanos nativos."""
    val = data.get(clave)
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "si", "yes")
    return bool(val)


# Alias con prefijo para compatibilidad con código interno previo
_extraer_str = extraer_str
_extraer_fecha = extraer_fecha
_extraer_bool = extraer_bool
