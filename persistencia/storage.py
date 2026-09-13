"""Módulo central de almacenamiento y persistencia unificada en formato JSON."""
from datetime import date, datetime, timezone
import json
import os
import shutil
from typing import Any, Dict

from diario.storage import libro_a_dict, libro_de_dict
from .exceptions import (
    EscrituraArchivoError,
    FormatoArchivoInvalidoError,
    IntegridadDatosError,
    PersistenciaError,
)
from .models import EjercicioContable
from .serializadores import (
    datos_empleado_a_dict,
    datos_empleado_de_dict,
    item_apertura_a_dict,
    item_apertura_de_dict,
    resultado_planilla_a_dict,
    resultado_planilla_de_dict,
    validar_integridad_contable,
)


def ejercicio_a_dict(ejercicio: EjercicioContable) -> Dict[str, Any]:
    """Convierte el EjercicioContable completo a estructura serializable JSON."""
    return {
        "formato": "ejercicio_contable_unificado",
        "version": ejercicio.version,
        "nombre_empresa": ejercicio.nombre_empresa,
        "nit": ejercicio.nit,
        "direccion": ejercicio.direccion,
        "moneda": ejercicio.moneda,
        "regimen_tributario": ejercicio.regimen_tributario,
        "contador_nombre": ejercicio.contador_nombre,
        "contador_registro": ejercicio.contador_registro,
        "periodo": ejercicio.periodo,
        "fecha_inicio": ejercicio.fecha_inicio.isoformat() if ejercicio.fecha_inicio else None,
        "fecha_fin": ejercicio.fecha_fin.isoformat() if ejercicio.fecha_fin else None,
        "cerrado": ejercicio.cerrado,
        "fecha_creacion": ejercicio.fecha_creacion,
        "fecha_modificacion": datetime.now(timezone.utc).isoformat(),
        "apertura": [item_apertura_a_dict(it) for it in ejercicio.items_apertura],
        "libro_diario": libro_a_dict(ejercicio.libro_diario),
        "empleados": [datos_empleado_a_dict(emp) for emp in ejercicio.empleados],
        "planillas": [resultado_planilla_a_dict(res) for res in ejercicio.planillas],
    }


def ejercicio_de_dict(data: Dict[str, Any], validar_integridad: bool = False) -> EjercicioContable:
    """
    Reconstruye un EjercicioContable a partir de un diccionario.
    Detecta automáticamente si la estructura es de formato unificado (v1.0 / v1.1) o de libro diario legado.
    """
    if not isinstance(data, dict):
        raise FormatoArchivoInvalidoError("La raíz del archivo contable debe ser un objeto JSON.")

    # Formato legado de solo libro diario (contiene 'partidas' en la raíz)
    if "partidas" in data and "libro_diario" not in data:
        libro = libro_de_dict(data)
        if validar_integridad:
            validar_integridad_contable(libro)
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

    if validar_integridad:
        validar_integridad_contable(libro)

    empleados = [datos_empleado_de_dict(emp) for emp in data.get("empleados", [])]
    planillas = [resultado_planilla_de_dict(res) for res in data.get("planillas", [])]

    f_inicio_str = data.get("fecha_inicio")
    f_fin_str = data.get("fecha_fin")
    fecha_inicio = date.fromisoformat(f_inicio_str) if f_inicio_str else None
    fecha_fin = date.fromisoformat(f_fin_str) if f_fin_str else None

    return EjercicioContable(
        version=str(data.get("version", "1.1")),
        nombre_empresa=str(data.get("nombre_empresa", "Empresa Ejemplo, S.A.")),
        nit=str(data.get("nit", "")),
        direccion=str(data.get("direccion", "")),
        moneda=str(data.get("moneda", "GTQ")),
        regimen_tributario=str(data.get("regimen_tributario", "Opcional Simplificado sobre Ingresos de Actividades Lucrativas")),
        contador_nombre=str(data.get("contador_nombre", "")),
        contador_registro=str(data.get("contador_registro", "")),
        periodo=str(data.get("periodo", "2026")),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        cerrado=bool(data.get("cerrado", False)),
        fecha_creacion=str(data.get("fecha_creacion", datetime.now(timezone.utc).isoformat())),
        fecha_modificacion=str(data.get("fecha_modificacion", datetime.now(timezone.utc).isoformat())),
        items_apertura=apertura_items,
        libro_diario=libro,
        empleados=empleados,
        planillas=planillas,
    )


def guardar_ejercicio_json(
    ejercicio: EjercicioContable,
    ruta_archivo: str,
    backup: bool = True,
) -> None:
    """
    Guarda el EjercicioContable completo en un archivo JSON de forma atómica y segura.
    
    - Crea automáticamente carpetas intermedias si no existen.
    - Crea respaldo `.bak` si el archivo ya existía.
    - Realiza escritura atómica en archivo `.tmp` antes de sustituir el archivo destino.
    """
    dir_destino = os.path.dirname(os.path.abspath(ruta_archivo))
    if dir_destino:
        try:
            os.makedirs(dir_destino, exist_ok=True)
        except OSError as exc:
            raise EscrituraArchivoError(f"No se pudo crear el directorio '{dir_destino}': {exc}") from exc

    # Respaldo de seguridad preventivo
    if backup and os.path.exists(ruta_archivo):
        ruta_bak = ruta_archivo + ".bak"
        try:
            shutil.copy2(ruta_archivo, ruta_bak)
        except OSError as exc:
            raise EscrituraArchivoError(f"Error al generar respaldo de seguridad '{ruta_bak}': {exc}") from exc

    # Escritura atómica
    data = ejercicio_a_dict(ejercicio)
    ruta_tmp = ruta_archivo + ".tmp"
    try:
        with open(ruta_tmp, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(ruta_tmp, ruta_archivo)
    except OSError as exc:
        if os.path.exists(ruta_tmp):
            try:
                os.remove(ruta_tmp)
            except OSError:
                pass
        raise EscrituraArchivoError(f"Error durante la escritura atómica en '{ruta_archivo}': {exc}") from exc


def cargar_ejercicio_json(ruta_archivo: str, validar_integridad: bool = False) -> EjercicioContable:
    """Carga un EjercicioContable desde un archivo JSON, con validación de formato y migración."""
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo de ejercicio contable: '{ruta_archivo}'")

    try:
        with open(ruta_archivo, mode="r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise FormatoArchivoInvalidoError(f"El archivo '{ruta_archivo}' contiene JSON malformado o corrupto: {exc}") from exc
    except OSError as exc:
        raise PersistenciaError(f"Error de E/S al leer '{ruta_archivo}': {exc}") from exc

    return ejercicio_de_dict(data, validar_integridad=validar_integridad)
