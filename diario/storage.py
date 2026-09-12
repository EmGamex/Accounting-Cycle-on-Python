"""Módulo de persistencia y serialización JSON para el Libro Diario."""
import json
from datetime import date
from decimal import Decimal
from typing import Any, Dict

from .models import LibroDiario, MovimientoLinea, PartidaDiario, TipoOrigenPartida


def linea_a_dict(linea: MovimientoLinea) -> Dict[str, Any]:
    """Convierte una línea contable a diccionario serializable."""
    return {
        "codigo": linea.codigo,
        "nombre": linea.nombre,
        "debe": str(linea.debe),
        "haber": str(linea.haber),
    }


def linea_de_dict(data: Dict[str, Any]) -> MovimientoLinea:
    """Reconstruye una línea contable desde un diccionario."""
    return MovimientoLinea(
        codigo=str(data["codigo"]),
        nombre=str(data["nombre"]),
        debe=Decimal(str(data.get("debe", "0.00"))),
        haber=Decimal(str(data.get("haber", "0.00"))),
    )


def partida_a_dict(partida: PartidaDiario) -> Dict[str, Any]:
    """Convierte una PartidaDiario a diccionario serializable."""
    return {
        "numero": partida.numero,
        "fecha": partida.fecha.isoformat(),
        "glosa": partida.glosa,
        "origen": partida.origen.value if isinstance(partida.origen, TipoOrigenPartida) else str(partida.origen),
        "documento_soporte": partida.documento_soporte,
        "lineas": [linea_a_dict(l) for l in partida.lineas],
    }


def partida_de_dict(data: Dict[str, Any]) -> PartidaDiario:
    """Reconstruye una PartidaDiario desde un diccionario."""
    fecha_dt = date.fromisoformat(data["fecha"])
    origen_val = data.get("origen", TipoOrigenPartida.MANUAL.value)
    try:
        origen_enum = TipoOrigenPartida(origen_val)
    except ValueError:
        origen_enum = TipoOrigenPartida.MANUAL

    lineas = [linea_de_dict(l) for l in data.get("lineas", [])]
    return PartidaDiario(
        numero=int(data["numero"]),
        fecha=fecha_dt,
        glosa=str(data.get("glosa", "")),
        lineas=lineas,
        origen=origen_enum,
        documento_soporte=data.get("documento_soporte"),
    )


def libro_a_dict(libro: LibroDiario) -> Dict[str, Any]:
    """Convierte el LibroDiario completo a estructura serializable."""
    return {
        "formato_version": "1.0",
        "total_debe": str(libro.total_debe),
        "total_haber": str(libro.total_haber),
        "cuadra": libro.cuadra,
        "partidas": [partida_a_dict(p) for p in libro.partidas],
    }


def libro_de_dict(data: Dict[str, Any]) -> LibroDiario:
    """Reconstruye un LibroDiario a partir de un diccionario."""
    partidas = [partida_de_dict(p) for p in data.get("partidas", [])]
    return LibroDiario(partidas=partidas)


def guardar_libro_json(libro: LibroDiario, ruta_archivo: str) -> None:
    """Guarda el LibroDiario en un archivo JSON en disco."""
    data = libro_a_dict(libro)
    with open(ruta_archivo, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cargar_libro_json(ruta_archivo: str) -> LibroDiario:
    """Carga un LibroDiario desde un archivo JSON."""
    with open(ruta_archivo, mode="r", encoding="utf-8") as f:
        data = json.load(f)
    return libro_de_dict(data)
