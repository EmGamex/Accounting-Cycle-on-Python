"""Modelos de datos fuertemente tipados para el Libro Diario."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Set

TWO_PLACES = Decimal("0.01")


class TipoOrigenPartida(str, Enum):
    """Clasificación del origen del asiento contable."""
    APERTURA = "APERTURA"
    PLANILLA = "PLANILLA"
    COMPRA = "COMPRA"
    VENTA = "VENTA"
    OPERACION = "OPERACION"
    AJUSTE = "AJUSTE"
    CIERRE = "CIERRE"
    MANUAL = "MANUAL"


@dataclass
class MovimientoLinea:
    """Línea individual de un asiento contable (cargo o abono)."""
    codigo: str
    nombre: str
    debe: Decimal = Decimal("0.00")
    haber: Decimal = Decimal("0.00")

    def __post_init__(self):
        if not isinstance(self.debe, Decimal):
            self.debe = Decimal(str(self.debe))
        if not isinstance(self.haber, Decimal):
            self.haber = Decimal(str(self.haber))

        self.debe = self.debe.quantize(TWO_PLACES)
        self.haber = self.haber.quantize(TWO_PLACES)

        if self.debe < Decimal("0.00"):
            raise ValueError(f"El debe no puede ser negativo: {self.debe}")
        if self.haber < Decimal("0.00"):
            raise ValueError(f"El haber no puede ser negativo: {self.haber}")
        if self.debe > Decimal("0.00") and self.haber > Decimal("0.00"):
            raise ValueError(
                f"Una línea no puede registrar simultáneamente Debe ({self.debe}) y Haber ({self.haber})."
            )

    @property
    def es_cargo(self) -> bool:
        """Indica si el movimiento representa un cargo al Debe."""
        return self.debe > Decimal("0.00")

    @property
    def es_abono(self) -> bool:
        """Indica si el movimiento representa un abono al Haber."""
        return self.haber > Decimal("0.00")

    @property
    def monto(self) -> Decimal:
        """Retorna el monto activo del movimiento (sea en Debe o en Haber)."""
        return self.debe if self.es_cargo else self.haber


@dataclass
class PartidaDiario:
    """Representa un asiento contable formal del Libro Diario."""
    numero: int
    fecha: date
    glosa: str
    lineas: List[MovimientoLinea] = field(default_factory=list)
    origen: TipoOrigenPartida = TipoOrigenPartida.MANUAL
    documento_soporte: Optional[str] = None

    @property
    def total_debe(self) -> Decimal:
        """Suma de todos los importes cargados al Debe."""
        return sum((l.debe for l in self.lineas), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def total_haber(self) -> Decimal:
        """Suma de todos los importes acreditados al Haber."""
        return sum((l.haber for l in self.lineas), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def cuadra(self) -> bool:
        """Verifica si el asiento cumple con el principio de partida doble."""
        return self.total_debe == self.total_haber and len(self.lineas) > 0

    @property
    def diferencia(self) -> Decimal:
        """Diferencia absoluta entre el total Debe y el total Haber."""
        return abs(self.total_debe - self.total_haber).quantize(TWO_PLACES)

    @property
    def cargos(self) -> List[MovimientoLinea]:
        """Lista de líneas con importes en el Debe."""
        return [l for l in self.lineas if l.es_cargo]

    @property
    def abonos(self) -> List[MovimientoLinea]:
        """Lista de líneas con importes en el Haber."""
        return [l for l in self.lineas if l.es_abono]

    def agregar_cargo(self, codigo: str, nombre: str, monto: Decimal) -> MovimientoLinea:
        """Agrega un cargo (Debe) a la partida."""
        linea = MovimientoLinea(codigo=codigo, nombre=nombre, debe=monto, haber=Decimal("0.00"))
        self.lineas.append(linea)
        return linea

    def agregar_abono(self, codigo: str, nombre: str, monto: Decimal) -> MovimientoLinea:
        """Agrega un abono (Haber) a la partida."""
        linea = MovimientoLinea(codigo=codigo, nombre=nombre, debe=Decimal("0.00"), haber=monto)
        self.lineas.append(linea)
        return linea


@dataclass
class LibroDiario:
    """Contenedor de asientos contables del ejercicio."""
    partidas: List[PartidaDiario] = field(default_factory=list)

    @property
    def total_debe(self) -> Decimal:
        """Suma acumulada de Debe de todas las partidas."""
        return sum((p.total_debe for p in self.partidas), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def total_haber(self) -> Decimal:
        """Suma acumulada de Haber de todas las partidas."""
        return sum((p.total_haber for p in self.partidas), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def cuadra(self) -> bool:
        """Verifica que el libro entero cuadre y todas sus partidas individuales cuadren."""
        return (self.total_debe == self.total_haber) and all(p.cuadra for p in self.partidas)

    @property
    def diferencia(self) -> Decimal:
        """Diferencia absoluta del libro diario."""
        return abs(self.total_debe - self.total_haber).quantize(TWO_PLACES)

    @property
    def cuentas_afectadas(self) -> Set[str]:
        """Conjunto de códigos de cuentas que han tenido movimiento en el libro."""
        cuentas = set()
        for p in self.partidas:
            for l in p.lineas:
                cuentas.add(l.codigo)
        return cuentas

    def obtener_partida(self, numero: int) -> Optional[PartidaDiario]:
        """Busca una partida por su número correlativo."""
        for p in self.partidas:
            if p.numero == numero:
                return p
        return None
