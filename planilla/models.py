"""Modelos de datos para empleados, resultados de cálculo y partidas contables."""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Tuple


@dataclass
class DatosEmpleado:
    """Estructura de entrada para los datos de un empleado."""
    nombre: str
    sueldo_base: Decimal
    departamento: str = "Administración"
    ventas: Decimal = Decimal("0.00")
    pct_comision: Decimal = Decimal("0.00")
    horas_extras: Decimal = Decimal("0.00")
    prestamos_deudas: Decimal = Decimal("0.00")
    otros_descuentos: Decimal = Decimal("0.00")
    isr_manual: Optional[Decimal] = None
    jornada_horas: Decimal = Decimal("8.0")


@dataclass
class ResultadoPlanilla:
    """Estructura para almacenar el cálculo y boleta final de un empleado."""
    empleado: str
    departamento: str
    sueldo_base: Decimal
    comisiones: Decimal
    horas_extras_trabajadas: Decimal
    sueldo_extraordinario: Decimal
    bonificacion_ley: Decimal
    total_afecto_igss: Decimal
    total_devengado: Decimal
    descuento_igss: Decimal
    descuento_isr: Decimal
    prestamos_deudas: Decimal
    otros_descuentos: Decimal
    total_descuentos: Decimal
    liquido_recibir: Decimal


@dataclass
class PartidaContable:
    """Estructura para almacenar el asiento contable consolidado."""
    debe: List[Tuple[str, Decimal]] = field(default_factory=list)
    haber: List[Tuple[str, Decimal]] = field(default_factory=list)
    total_debe: Decimal = Decimal("0.00")
    total_haber: Decimal = Decimal("0.00")
    cuadra: bool = True
    diferencia: Decimal = Decimal("0.00")
