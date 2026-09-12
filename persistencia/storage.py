"""Módulo central de almacenamiento y persistencia unificada en formato JSON."""
import json
from datetime import datetime, timezone
from typing import Any, Dict

from diario.storage import libro_a_dict, libro_de_dict
from .models import EjercicioContable
from .serializadores import (
    datos_empleado_a_dict,
    datos_empleado_de_dict,
    item_apertura_a_dict,
    item_apertura_de_dict,
    resultado_planilla_a_dict,
    resultado_planilla_de_dict,
)


def ejercicio_a_dict(ejercicio: EjercicioContable) -> Dict[str, Any]:
    """Convierte el EjercicioContable completo a estructura serializable JSON."""
    return {
        "formato": "ejercicio_contable_unificado",
        "version": ejercicio.version,
        "nombre_empresa": ejercicio.nombre_empresa,
        "periodo": ejercicio.periodo,
        "fecha_modificacion": datetime.now(timezone.utc).isoformat(),
        "apertura": [item_apertura_a_dict(it) for it in ejercicio.items_apertura],
        "libro_diario": libro_a_dict(ejercicio.libro_diario),
        "empleados": [datos_empleado_a_dict(emp) for emp in ejercicio.empleados],
        "planillas": [resultado_planilla_a_dict(res) for res in ejercicio.planillas],
    }


def ejercicio_de_dict(data: Dict[str, Any]) -> EjercicioContable:
    """
    Reconstruye un EjercicioContable a partir de un diccionario.
    Detecta automáticamente si la estructura es de formato unificado o de libro diario legado.
    """
    # Si es formato legado de solo libro diario (contiene 'partidas' en la raíz)
    if "partidas" in data and "libro_diario" not in data:
        libro = libro_de_dict(data)
        return EjercicioContable(
            version="1.0",
            nombre_empresa="Empresa Sin Nombre",
            periodo="2026",
            libro_diario=libro,
        )

    # Formato unificado
    apertura_items = [item_apertura_de_dict(it) for it in data.get("apertura", [])]
    diario_data = data.get("libro_diario", {})
    libro = libro_de_dict(diario_data) if diario_data else libro_de_dict({"partidas": []})
    empleados = [datos_empleado_de_dict(emp) for emp in data.get("empleados", [])]
    planillas = [resultado_planilla_de_dict(res) for res in data.get("planillas", [])]

    return EjercicioContable(
        version=str(data.get("version", "1.0")),
        nombre_empresa=str(data.get("nombre_empresa", "Empresa Ejemplo, S.A.")),
        periodo=str(data.get("periodo", "2026")),
        fecha_modificacion=str(data.get("fecha_modificacion", datetime.now(timezone.utc).isoformat())),
        items_apertura=apertura_items,
        libro_diario=libro,
        empleados=empleados,
        planillas=planillas,
    )


def guardar_ejercicio_json(ejercicio: EjercicioContable, ruta_archivo: str) -> None:
    """Guarda el EjercicioContable completo en un archivo JSON."""
    data = ejercicio_a_dict(ejercicio)
    with open(ruta_archivo, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cargar_ejercicio_json(ruta_archivo: str) -> EjercicioContable:
    """Carga un EjercicioContable desde un archivo JSON, con detección de formatos legados."""
    with open(ruta_archivo, mode="r", encoding="utf-8") as f:
        data = json.load(f)
    return ejercicio_de_dict(data)
