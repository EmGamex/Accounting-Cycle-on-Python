"""Modelos de datos fuertemente tipados para la persistencia unificada del Ejercicio Contable."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from apertura.models import ItemCuentaApertura
from diario.models import LibroDiario
from planilla.models import DatosEmpleado, ResultadoPlanilla


@dataclass
class EjercicioContable:
    """Estructura raíz que agrupa el estado global de todos los módulos contables."""
    version: str = "1.0"
    nombre_empresa: str = "Empresa Ejemplo, S.A."
    periodo: str = "2026"
    fecha_modificacion: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    items_apertura: List[ItemCuentaApertura] = field(default_factory=list)
    libro_diario: LibroDiario = field(default_factory=LibroDiario)
    empleados: List[DatosEmpleado] = field(default_factory=list)
    planillas: List[ResultadoPlanilla] = field(default_factory=list)
