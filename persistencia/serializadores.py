"""Serializadores y deserializadores para transformar modelos a diccionarios y viceversa."""
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from apertura.models import ItemCuentaApertura
from diario.storage import libro_a_dict, libro_de_dict
from planilla.models import DatosEmpleado, ResultadoPlanilla
from .exceptions import FormatoArchivoInvalidoError, IntegridadDatosError


def item_apertura_a_dict(item: ItemCuentaApertura) -> Dict[str, Any]:
    """Convierte un ItemCuentaApertura a diccionario serializable."""
    return {
        "codigo": item.codigo,
        "nombre": item.nombre,
        "monto": str(item.monto),
        "clase": item.clase,
        "subgrupo": item.subgrupo,
        "es_regularizadora": item.es_regularizadora,
    }


def item_apertura_de_dict(data: Dict[str, Any]) -> ItemCuentaApertura:
    """Reconstruye un ItemCuentaApertura desde un diccionario validando campos obligatorios."""
    if not isinstance(data, dict):
        raise FormatoArchivoInvalidoError("Los datos de ItemCuentaApertura deben ser un diccionario.")
    if "codigo" not in data or "monto" not in data:
        raise FormatoArchivoInvalidoError("ItemCuentaApertura requiere al menos 'codigo' y 'monto'.")

    try:
        monto_dec = Decimal(str(data["monto"]))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FormatoArchivoInvalidoError(f"Monto inválido para cuenta '{data.get('codigo')}': {data.get('monto')}") from exc

    return ItemCuentaApertura(
        codigo=str(data["codigo"]),
        nombre=str(data.get("nombre", "")),
        monto=monto_dec,
        clase=str(data.get("clase", "")),
        subgrupo=str(data.get("subgrupo", "")),
        es_regularizadora=bool(data.get("es_regularizadora", False)),
    )


def datos_empleado_a_dict(emp: DatosEmpleado) -> Dict[str, Any]:
    """Convierte un DatosEmpleado a diccionario serializable."""
    return {
        "nombre": emp.nombre,
        "departamento": emp.departamento,
        "sueldo_base": str(emp.sueldo_base),
        "ventas": str(emp.ventas),
        "pct_comision": str(emp.pct_comision),
        "horas_extras": str(emp.horas_extras),
        "prestamos_deudas": str(emp.prestamos_deudas),
        "otros_descuentos": str(emp.otros_descuentos),
        "isr_manual": str(emp.isr_manual) if emp.isr_manual is not None else None,
        "jornada_horas": str(emp.jornada_horas),
    }


def datos_empleado_de_dict(data: Dict[str, Any]) -> DatosEmpleado:
    """Reconstruye un DatosEmpleado desde un diccionario con validación de tipos Decimal."""
    if not isinstance(data, dict):
        raise FormatoArchivoInvalidoError("Los datos de empleado deben ser un diccionario.")
    if "nombre" not in data:
        raise FormatoArchivoInvalidoError("El registro de empleado requiere el campo 'nombre'.")

    isr = data.get("isr_manual")
    try:
        return DatosEmpleado(
            nombre=str(data["nombre"]),
            departamento=str(data.get("departamento", "Administración")),
            sueldo_base=Decimal(str(data.get("sueldo_base", "0.00"))),
            ventas=Decimal(str(data.get("ventas", "0.00"))),
            pct_comision=Decimal(str(data.get("pct_comision", "0.00"))),
            horas_extras=Decimal(str(data.get("horas_extras", "0.00"))),
            prestamos_deudas=Decimal(str(data.get("prestamos_deudas", "0.00"))),
            otros_descuentos=Decimal(str(data.get("otros_descuentos", "0.00"))),
            isr_manual=Decimal(str(isr)) if isr is not None else None,
            jornada_horas=Decimal(str(data.get("jornada_horas", "8.0"))),
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FormatoArchivoInvalidoError(f"Error numérico al procesar empleado '{data.get('nombre')}': {exc}") from exc


def resultado_planilla_a_dict(res: ResultadoPlanilla) -> Dict[str, Any]:
    """Convierte un ResultadoPlanilla a diccionario serializable."""
    return {
        "empleado": res.empleado,
        "departamento": res.departamento,
        "sueldo_base": str(res.sueldo_base),
        "comisiones": str(res.comisiones),
        "horas_extras_trabajadas": str(res.horas_extras_trabajadas),
        "sueldo_extraordinario": str(res.sueldo_extraordinario),
        "bonificacion_ley": str(res.bonificacion_ley),
        "total_afecto_igss": str(res.total_afecto_igss),
        "total_devengado": str(res.total_devengado),
        "descuento_igss": str(res.descuento_igss),
        "descuento_isr": str(res.descuento_isr),
        "prestamos_deudas": str(res.prestamos_deudas),
        "otros_descuentos": str(res.otros_descuentos),
        "total_descuentos": str(res.total_descuentos),
        "liquido_recibir": str(res.liquido_recibir),
    }


def resultado_planilla_de_dict(data: Dict[str, Any]) -> ResultadoPlanilla:
    """Reconstruye un ResultadoPlanilla desde un diccionario."""
    if not isinstance(data, dict):
        raise FormatoArchivoInvalidoError("Los datos de planilla deben ser un diccionario.")
    if "empleado" not in data:
        raise FormatoArchivoInvalidoError("El resultado de planilla requiere el campo 'empleado'.")

    try:
        return ResultadoPlanilla(
            empleado=str(data["empleado"]),
            departamento=str(data.get("departamento", "Administración")),
            sueldo_base=Decimal(str(data.get("sueldo_base", "0.00"))),
            comisiones=Decimal(str(data.get("comisiones", "0.00"))),
            horas_extras_trabajadas=Decimal(str(data.get("horas_extras_trabajadas", "0.00"))),
            sueldo_extraordinario=Decimal(str(data.get("sueldo_extraordinario", "0.00"))),
            bonificacion_ley=Decimal(str(data.get("bonificacion_ley", "0.00"))),
            total_afecto_igss=Decimal(str(data.get("total_afecto_igss", "0.00"))),
            total_devengado=Decimal(str(data.get("total_devengado", "0.00"))),
            descuento_igss=Decimal(str(data.get("descuento_igss", "0.00"))),
            descuento_isr=Decimal(str(data.get("descuento_isr", "0.00"))),
            prestamos_deudas=Decimal(str(data.get("prestamos_deudas", "0.00"))),
            otros_descuentos=Decimal(str(data.get("otros_descuentos", "0.00"))),
            total_descuentos=Decimal(str(data.get("total_descuentos", "0.00"))),
            liquido_recibir=Decimal(str(data.get("liquido_recibir", "0.00"))),
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FormatoArchivoInvalidoError(f"Error numérico en boleta de '{data.get('empleado')}': {exc}") from exc


def validar_integridad_contable(libro) -> None:
    """Verifica que todas las partidas del libro diario cumplan con la partida doble."""
    for partida in libro.partidas:
        if not partida.cuadra:
            raise IntegridadDatosError(
                f"La Partida No. {partida.numero} del Libro Diario está descuadrada: "
                f"Debe={partida.total_debe}, Haber={partida.total_haber}, Diferencia={partida.diferencia}"
            )
