"""Módulo de operaciones seguras de entrada/salida (I/O) en disco para persistencia."""
import json
import os
import shutil
from typing import Union

from .exceptions import (
    EscrituraArchivoError,
    FormatoArchivoInvalidoError,
    PersistenciaError,
)
from .models import EjercicioContable
from .serializadores import ejercicio_a_dict, ejercicio_de_dict

RutaArchivo = Union[str, os.PathLike[str]]


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
