"""Paquete de persistencia unificada para el Sistema Contable Integral."""
from .models import EjercicioContable
from .serializadores import (
    datos_empleado_a_dict,
    datos_empleado_de_dict,
    item_apertura_a_dict,
    item_apertura_de_dict,
    resultado_planilla_a_dict,
    resultado_planilla_de_dict,
)
from .storage import (
    cargar_ejercicio_json,
    ejercicio_a_dict,
    ejercicio_de_dict,
    guardar_ejercicio_json,
)

__all__ = [
    "EjercicioContable",
    "item_apertura_a_dict",
    "item_apertura_de_dict",
    "datos_empleado_a_dict",
    "datos_empleado_de_dict",
    "resultado_planilla_a_dict",
    "resultado_planilla_de_dict",
    "ejercicio_a_dict",
    "ejercicio_de_dict",
    "guardar_ejercicio_json",
    "cargar_ejercicio_json",
]
