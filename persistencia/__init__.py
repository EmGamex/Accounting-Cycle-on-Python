"""Paquete de persistencia unificada para el Sistema Contable Integral."""
from .exceptions import (
    EscrituraArchivoError,
    FormatoArchivoInvalidoError,
    IntegridadDatosError,
    PersistenciaError,
    VersionEsquemaIncompatibleError,
)
from .helpers import (
    extraer_bool,
    extraer_fecha,
    extraer_str,
)
from .io import (
    RutaArchivo,
    cargar_ejercicio_json,
    guardar_ejercicio_json,
)
from .models import EjercicioContable
from .serializadores import (
    VERSION_ACTUAL_MAYOR,
    datos_empleado_a_dict,
    datos_empleado_de_dict,
    ejercicio_a_dict,
    ejercicio_de_dict,
    item_apertura_a_dict,
    item_apertura_de_dict,
    resultado_planilla_a_dict,
    resultado_planilla_de_dict,
)
from .validadores import validar_integridad_contable

__all__ = [
    "EjercicioContable",
    "PersistenciaError",
    "FormatoArchivoInvalidoError",
    "VersionEsquemaIncompatibleError",
    "IntegridadDatosError",
    "EscrituraArchivoError",
    "RutaArchivo",
    "VERSION_ACTUAL_MAYOR",
    "item_apertura_a_dict",
    "item_apertura_de_dict",
    "datos_empleado_a_dict",
    "datos_empleado_de_dict",
    "resultado_planilla_a_dict",
    "resultado_planilla_de_dict",
    "validar_integridad_contable",
    "ejercicio_a_dict",
    "ejercicio_de_dict",
    "guardar_ejercicio_json",
    "cargar_ejercicio_json",
    "extraer_str",
    "extraer_fecha",
    "extraer_bool",
]
