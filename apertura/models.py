"""Modelos de datos fuertemente tipados para el sistema de apertura contable."""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional


@dataclass
class CuentaCatalogo:
    codigo: str
    nombre: str
    nombre_norm: str
    clase: str
    subgrupo: str
    es_regularizadora: bool = False


@dataclass
class ItemCuentaApertura:
    codigo: str
    nombre: str
    monto: Decimal
    clase: str
    subgrupo: str
    es_regularizadora: bool = False


@dataclass
class LineaPartida:
    codigo: str
    nombre: str
    debe: Decimal = Decimal("0.00")
    haber: Decimal = Decimal("0.00")


@dataclass
class PartidaApertura:
    numero: int
    descripcion: str
    lineas: List[LineaPartida] = field(default_factory=list)
    total_debe: Decimal = Decimal("0.00")
    total_haber: Decimal = Decimal("0.00")

    @property
    def cuadra(self) -> bool:
        return self.total_debe == self.total_haber

    @property
    def diferencia(self) -> Decimal:
        return abs(self.total_debe - self.total_haber)


@dataclass
class ResumenBalance:
    total_activo: Decimal
    total_pasivo: Decimal
    total_patrimonio: Decimal
    diferencia_capital: Decimal
    estructura_balance: Dict[str, Dict[str, Dict[str, ItemCuentaApertura]]]

    @property
    def total_pasivo_y_patrimonio(self) -> Decimal:
        return self.total_pasivo + self.total_patrimonio

    @property
    def cuadra(self) -> bool:
        return self.total_activo == self.total_pasivo_y_patrimonio
