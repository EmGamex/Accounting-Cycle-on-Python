"""Modelos de datos fuertemente tipados para la persistencia unificada del Ejercicio Contable."""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, List, Optional

from apertura.models import ItemCuentaApertura
from diario.models import LibroDiario
from planilla.models import DatosEmpleado, ResultadoPlanilla


@dataclass
class EjercicioContable:
    """Estructura raíz que agrupa el estado global de todos los módulos contables."""
    version: str = "1.1"
    nombre_empresa: str = "Empresa Ejemplo, S.A."
    nit: str = ""
    direccion: str = ""
    moneda: str = "GTQ"
    regimen_tributario: str = "Opcional Simplificado sobre Ingresos de Actividades Lucrativas"
    contador_nombre: str = ""
    contador_registro: str = ""
    periodo: str = "2026"
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    cerrado: bool = False
    fecha_creacion: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    fecha_modificacion: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    items_apertura: List[ItemCuentaApertura] = field(default_factory=list)
    libro_diario: LibroDiario = field(default_factory=LibroDiario)
    empleados: List[DatosEmpleado] = field(default_factory=list)
    planillas: List[ResultadoPlanilla] = field(default_factory=list)

    @property
    def cuadra(self) -> bool:
        """Indica si el libro diario del ejercicio está debidamente balanceado."""
        return self.libro_diario.cuadra

    def generar_mayor(self) -> Any:
        """Genera el Libro Mayor derivado a partir de las partidas del Libro Diario."""
        from mayor.engine import mayorizar_libro_diario
        return mayorizar_libro_diario(self.libro_diario)

    def generar_balance_4_columnas(self) -> Any:
        """Genera el Balance de 4 Columnas derivado a partir del Libro Mayor o Libro Diario."""
        from balance.engine import generar_balance_4_columnas
        return generar_balance_4_columnas(
            self.libro_diario,
            empresa=self.nombre_empresa,
            periodo=self.periodo,
        )
