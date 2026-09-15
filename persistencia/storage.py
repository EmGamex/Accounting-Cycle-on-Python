"""Módulo central de almacenamiento y persistencia unificada en formato JSON."""
from datetime import date, datetime, timezone
import json
import os
import shutil
from typing import Any, Dict, Optional, Union

from diario.storage import libro_a_dict, libro_de_dict
from .exceptions import (
    EscrituraArchivoError,
    FormatoArchivoInvalidoError,
    PersistenciaError,
    VersionEsquemaIncompatibleError,
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

RutaArchivo = Union[str, os.PathLike[str]]
VERSION_ACTUAL_MAYOR = 1


def _extraer_str(data: Dict[str, Any], clave: str, default: str = "") -> str:
    """Extrae un string de forma segura evitando convertir None en 'None'."""
    val = data.get(clave)
    return str(val) if val is not None else default


def _extraer_fecha(data: Dict[str, Any], clave: str) -> Optional[date]:
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


def _extraer_bool(data: Dict[str, Any], clave: str, default: bool = False) -> bool:
    """Extrae un valor booleano manejando cadenas 'true'/'false' y booleanos nativos."""
    val = data.get(clave)
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "si", "yes")
    return bool(val)


def ejercicio_a_dict(ejercicio: EjercicioContable) -> Dict[str, Any]:
    """Convierte el EjercicioContable completo a estructura serializable JSON."""
    ahora_utc = datetime.now(timezone.utc).isoformat()
    ejercicio.fecha_modificacion = ahora_utc

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
        "fecha_modificacion": ahora_utc,
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

    # Validación preventiva de versión mayor
    ver_str = _extraer_str(data, "version", "1.1")
    try:
        ver_mayor = int(ver_str.split(".")[0])
        if ver_mayor > VERSION_ACTUAL_MAYOR:
            raise VersionEsquemaIncompatibleError(
                f"La versión del esquema '{ver_str}' es incompatible con esta aplicación (soporta v{VERSION_ACTUAL_MAYOR}.x)."
            )
    except ValueError:
        pass

    raw_apertura = data.get("apertura") or []
    if not isinstance(raw_apertura, list):
        raise FormatoArchivoInvalidoError("El campo 'apertura' debe ser una lista.")
    apertura_items = [item_apertura_de_dict(it) for it in raw_apertura]

    diario_data = data.get("libro_diario")
    libro = libro_de_dict(diario_data) if isinstance(diario_data, dict) else libro_de_dict({"partidas": []})

    if validar_integridad:
        validar_integridad_contable(libro)

    raw_empleados = data.get("empleados") or []
    if not isinstance(raw_empleados, list):
        raise FormatoArchivoInvalidoError("El campo 'empleados' debe ser una lista.")
    empleados = [datos_empleado_de_dict(emp) for emp in raw_empleados]

    raw_planillas = data.get("planillas") or []
    if not isinstance(raw_planillas, list):
        raise FormatoArchivoInvalidoError("El campo 'planillas' debe ser una lista.")
    planillas = [resultado_planilla_de_dict(res) for res in raw_planillas]

    ahora_default = datetime.now(timezone.utc).isoformat()

    return EjercicioContable(
        version=ver_str,
        nombre_empresa=_extraer_str(data, "nombre_empresa", "Empresa Ejemplo, S.A."),
        nit=_extraer_str(data, "nit", ""),
        direccion=_extraer_str(data, "direccion", ""),
        moneda=_extraer_str(data, "moneda", "GTQ"),
        regimen_tributario=_extraer_str(
            data, "regimen_tributario", "Opcional Simplificado sobre Ingresos de Actividades Lucrativas"
        ),
        contador_nombre=_extraer_str(data, "contador_nombre", ""),
        contador_registro=_extraer_str(data, "contador_registro", ""),
        periodo=_extraer_str(data, "periodo", "2026"),
        fecha_inicio=_extraer_fecha(data, "fecha_inicio"),
        fecha_fin=_extraer_fecha(data, "fecha_fin"),
        cerrado=_extraer_bool(data, "cerrado", False),
        fecha_creacion=_extraer_str(data, "fecha_creacion", ahora_default),
        fecha_modificacion=_extraer_str(data, "fecha_modificacion", ahora_default),
        items_apertura=apertura_items,
        libro_diario=libro,
        empleados=empleados,
        planillas=planillas,
    )


def guardar_ejercicio_json(
    ejercicio: EjercicioContable,
    ruta_archivo: RutaArchivo,
    backup: bool = True,
) -> None:
    """
    Guarda el EjercicioContable completo en un archivo JSON de forma atómica y segura.
    
    - Soporta tanto `str` como `pathlib.Path`.
    - Crea automáticamente carpetas intermedias si no existen.
    - Crea respaldo `.bak` si el archivo ya existía.
    - Realiza escritura atómica en archivo temporal antes de sustituir el destino.
    """
    ruta_str = os.fspath(ruta_archivo)
    dir_destino = os.path.dirname(os.path.abspath(ruta_str))
    if dir_destino:
        try:
            os.makedirs(dir_destino, exist_ok=True)
        except OSError as exc:
            raise EscrituraArchivoError(f"No se pudo crear el directorio '{dir_destino}': {exc}") from exc

    if backup and os.path.isfile(ruta_str):
        ruta_bak = f"{ruta_str}.bak"
        try:
            shutil.copy2(ruta_str, ruta_bak)
        except OSError as exc:
            raise EscrituraArchivoError(f"Error al generar respaldo de seguridad '{ruta_bak}': {exc}") from exc

    data = ejercicio_a_dict(ejercicio)
    ruta_tmp = f"{ruta_str}.{os.getpid()}.tmp"
    escritura_exitosa = False

    try:
        with open(ruta_tmp, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(ruta_tmp, ruta_str)
        escritura_exitosa = True
    except OSError as exc:
        raise EscrituraArchivoError(f"Error durante la escritura atómica en '{ruta_str}': {exc}") from exc
    except Exception as exc:
        raise EscrituraArchivoError(f"Error de serialización al guardar '{ruta_str}': {exc}") from exc
    finally:
        if not escritura_exitosa and os.path.exists(ruta_tmp):
            try:
                os.remove(ruta_tmp)
            except OSError:
                pass


def cargar_ejercicio_json(ruta_archivo: RutaArchivo, validar_integridad: bool = False) -> EjercicioContable:
    """Carga un EjercicioContable desde un archivo JSON, con validación de formato y migración."""
    ruta_str = os.fspath(ruta_archivo)
    try:
        with open(ruta_str, mode="r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo de ejercicio contable: '{ruta_str}'")
    except json.JSONDecodeError as exc:
        raise FormatoArchivoInvalidoError(f"El archivo '{ruta_str}' contiene JSON malformado o corrupto: {exc}") from exc
    except OSError as exc:
        raise PersistenciaError(f"Error de E/S al leer '{ruta_str}': {exc}") from exc

    return ejercicio_de_dict(data, validar_integridad=validar_integridad)
