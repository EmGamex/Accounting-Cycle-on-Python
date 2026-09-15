"""Módulo de fachada y compatibilidad para almacenamiento y persistencia."""
from .helpers import (
    extraer_bool,
    extraer_fecha,
    extraer_str,
    _extraer_bool,
    _extraer_fecha,
    _extraer_str,
)
from .io import (
    RutaArchivo,
    cargar_ejercicio_json,
    guardar_ejercicio_json,
)
from .serializadores import (
    VERSION_ACTUAL_MAYOR,
    ejercicio_a_dict,
    ejercicio_de_dict,
)

__all__ = [
    "RutaArchivo",
    "VERSION_ACTUAL_MAYOR",
    "ejercicio_a_dict",
    "ejercicio_de_dict",
    "guardar_ejercicio_json",
    "cargar_ejercicio_json",
    "extraer_str",
    "extraer_fecha",
    "extraer_bool",
    "_extraer_str",
    "_extraer_fecha",
    "_extraer_bool",
]
