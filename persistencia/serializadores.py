"""Serializadores y deserializadores para transformar modelos a diccionarios y viceversa."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from apertura.models import ItemCuentaApertura
from diario.storage import libro_a_dict, libro_de_dict
from planilla.models import DatosEmpleado, ResultadoPlanilla
from .exceptions import (
    FormatoArchivoInvalidoError,
    IntegridadDatosError,
    VersionEsquemaIncompatibleError,
)
from .helpers import extraer_bool, extraer_fecha, extraer_str
from .models import EjercicioContable
from .validadores import validar_integridad_contable

VERSION_ACTUAL_MAYOR = 1


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

    ver_str = extraer_str(data, "version", "1.1")
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
        nombre_empresa=extraer_str(data, "nombre_empresa", "Empresa Ejemplo, S.A."),
        nit=extraer_str(data, "nit", ""),
        direccion=extraer_str(data, "direccion", ""),
        moneda=extraer_str(data, "moneda", "GTQ"),
        regimen_tributario=extraer_str(
            data, "regimen_tributario", "Opcional Simplificado sobre Ingresos de Actividades Lucrativas"
        ),
        contador_nombre=extraer_str(data, "contador_nombre", ""),
        contador_registro=extraer_str(data, "contador_registro", ""),
        periodo=extraer_str(data, "periodo", "2026"),
        fecha_inicio=extraer_fecha(data, "fecha_inicio"),
        fecha_fin=extraer_fecha(data, "fecha_fin"),
        cerrado=extraer_bool(data, "cerrado", False),
        fecha_creacion=extraer_str(data, "fecha_creacion", ahora_default),
        fecha_modificacion=extraer_str(data, "fecha_modificacion", ahora_default),
        items_apertura=apertura_items,
        libro_diario=libro,
        empleados=empleados,
        planillas=planillas,
    )
