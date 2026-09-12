"""Modelos de datos fuertemente tipados para el Libro Mayor y T-Gráficas."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

TWO_PLACES = Decimal("0.01")


class NaturalezaSaldo(str, Enum):
    """Naturaleza y estado del saldo contable."""
    DEUDOR = "DEUDOR"
    ACREEDOR = "ACREEDOR"
    SALDADA = "SALDADA"


@dataclass
class MovimientoMayor:
    """Representa un pase individual del Libro Diario hacia una cuenta del Mayor."""
    numero_partida: int
    fecha: date
    concepto: str
    debe: Decimal = Decimal("0.00")
    haber: Decimal = Decimal("0.00")
    documento_soporte: Optional[str] = None
    saldo_acumulado: Decimal = Decimal("0.00")

    def __post_init__(self):
        if not isinstance(self.debe, Decimal):
            self.debe = Decimal(str(self.debe))
        if not isinstance(self.haber, Decimal):
            self.haber = Decimal(str(self.haber))
        if not isinstance(self.saldo_acumulado, Decimal):
            self.saldo_acumulado = Decimal(str(self.saldo_acumulado))

        self.debe = self.debe.quantize(TWO_PLACES)
        self.haber = self.haber.quantize(TWO_PLACES)
        self.saldo_acumulado = self.saldo_acumulado.quantize(TWO_PLACES)

        if self.debe < Decimal("0.00"):
            raise ValueError(f"El debe no puede ser negativo: {self.debe}")
        if self.haber < Decimal("0.00"):
            raise ValueError(f"El haber no puede ser negativo: {self.haber}")
        if self.debe > Decimal("0.00") and self.haber > Decimal("0.00"):
            raise ValueError(
                f"Un movimiento no puede registrar simultáneamente Debe ({self.debe}) y Haber ({self.haber})."
            )

    @property
    def es_cargo(self) -> bool:
        """Indica si el movimiento es un débito / cargo al Debe."""
        return self.debe > Decimal("0.00")

    @property
    def es_abono(self) -> bool:
        """Indica si el movimiento es un crédito / abono al Haber."""
        return self.haber > Decimal("0.00")

    @property
    def monto(self) -> Decimal:
        """Retorna el valor numérico activo del movimiento."""
        return self.debe if self.es_cargo else self.haber


@dataclass
class CuentaMayor:
    """Acumulador formal de movimientos y determinación de saldos para una cuenta."""
    codigo: str
    nombre: str
    movimientos: List[MovimientoMayor] = field(default_factory=list)

    @property
    def cargos(self) -> List[MovimientoMayor]:
        """Lista de movimientos imputados al Debe."""
        return [m for m in self.movimientos if m.es_cargo]

    @property
    def abonos(self) -> List[MovimientoMayor]:
        """Lista de movimientos imputados al Haber."""
        return [m for m in self.movimientos if m.es_abono]

    @property
    def total_debe(self) -> Decimal:
        """Suma aritmética de cargos cargados en la cuenta."""
        return sum((m.debe for m in self.movimientos), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def total_haber(self) -> Decimal:
        """Suma aritmética de abonos acreditados en la cuenta."""
        return sum((m.haber for m in self.movimientos), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def saldo(self) -> Decimal:
        """Magnitud absoluta de la diferencia entre Debe y Haber."""
        return abs(self.total_debe - self.total_haber).quantize(TWO_PLACES)

    @property
    def tipo_saldo(self) -> NaturalezaSaldo:
        """Determina si la cuenta tiene saldo deudor, acreedor o está saldada."""
        if self.total_debe > self.total_haber:
            return NaturalezaSaldo.DEUDOR
        elif self.total_haber > self.total_debe:
            return NaturalezaSaldo.ACREEDOR
        return NaturalezaSaldo.SALDADA

    @property
    def saldo_deudor(self) -> Decimal:
        """Monto del saldo si es deudor, o 0.00 en caso contrario."""
        return self.saldo if self.tipo_saldo == NaturalezaSaldo.DEUDOR else Decimal("0.00")

    @property
    def saldo_acreedor(self) -> Decimal:
        """Monto del saldo si es acreedor, o 0.00 en caso contrario."""
        return self.saldo if self.tipo_saldo == NaturalezaSaldo.ACREEDOR else Decimal("0.00")

    @property
    def naturaleza_esperada(self) -> NaturalezaSaldo:
        """Infiere la naturaleza esperada según el código contable guatemalteco."""
        cod = self.codigo.strip()
        if "-R" in cod or cod.startswith("1205") or cod.startswith("1210"):
            return NaturalezaSaldo.ACREEDOR
        if cod.startswith("4103") or cod.startswith("3104"):
            return NaturalezaSaldo.DEUDOR
        if cod.startswith("1") or cod.startswith("5"):
            return NaturalezaSaldo.DEUDOR
        return NaturalezaSaldo.ACREEDOR

    @property
    def es_saldo_anomalo(self) -> bool:
        """Indica si el saldo no nulo es opuesto a la naturaleza contable esperada."""
        if self.tipo_saldo == NaturalezaSaldo.SALDADA:
            return False
        return self.tipo_saldo != self.naturaleza_esperada

    def calcular_movimientos_con_saldo(self) -> List[MovimientoMayor]:
        """Calcula el saldo acumulado cronológico para presentación a 3 columnas."""
        resultado = []
        saldo_actual = Decimal("0.00")
        es_acreedora = (self.naturaleza_esperada == NaturalezaSaldo.ACREEDOR)

        for m in sorted(self.movimientos, key=lambda x: (x.fecha, x.numero_partida)):
            if es_acreedora:
                saldo_actual += (m.haber - m.debe)
            else:
                saldo_actual += (m.debe - m.haber)

            copia = MovimientoMayor(
                numero_partida=m.numero_partida,
                fecha=m.fecha,
                concepto=m.concepto,
                debe=m.debe,
                haber=m.haber,
                documento_soporte=m.documento_soporte,
                saldo_acumulado=saldo_actual.quantize(TWO_PLACES),
            )
            resultado.append(copia)
        return resultado


@dataclass
class LibroMayor:
    """Contenedor de cuentas mayorizadas del ejercicio."""
    cuentas: Dict[str, CuentaMayor] = field(default_factory=dict)

    @property
    def total_debe(self) -> Decimal:
        """Suma de Debe de todas las cuentas del mayor."""
        return sum((c.total_debe for c in self.cuentas.values()), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def total_haber(self) -> Decimal:
        """Suma de Haber de todas las cuentas del mayor."""
        return sum((c.total_haber for c in self.cuentas.values()), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def total_saldos_deudores(self) -> Decimal:
        """Suma acumulada de todos los saldos deudores."""
        return sum((c.saldo_deudor for c in self.cuentas.values()), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def total_saldos_acreedores(self) -> Decimal:
        """Suma acumulada de todos los saldos acreedores."""
        return sum((c.saldo_acreedor for c in self.cuentas.values()), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def cuadra(self) -> bool:
        """Verifica la doble condición de cuadre: sumas iguales y saldos iguales."""
        sumas_iguales = (self.total_debe == self.total_haber)
        saldos_iguales = (self.total_saldos_deudores == self.total_saldos_acreedores)
        return sumas_iguales and saldos_iguales

    @property
    def diferencia_sumas(self) -> Decimal:
        """Diferencia absoluta entre total Debe y total Haber."""
        return abs(self.total_debe - self.total_haber).quantize(TWO_PLACES)

    @property
    def diferencia_saldos(self) -> Decimal:
        """Diferencia absoluta entre total Saldos Deudores y total Saldos Acreedores."""
        return abs(self.total_saldos_deudores - self.total_saldos_acreedores).quantize(TWO_PLACES)

    @property
    def cuentas_ordenadas(self) -> List[CuentaMayor]:
        """Lista de cuentas ordenadas numéricamente según la jerarquía contable."""
        def clave_orden(c: CuentaMayor) -> tuple:
            partes = c.codigo.split("-")
            primera = partes[0]
            num = int(primera) if primera.isdigit() else 9999
            return (num, c.codigo)

        return sorted(self.cuentas.values(), key=clave_orden)

    def obtener_cuenta(self, codigo: str) -> Optional[CuentaMayor]:
        """Busca una cuenta por su código contable."""
        return self.cuentas.get(codigo.strip())

    def buscar_cuentas(self, termino: str) -> List[CuentaMayor]:
        """Filtra cuentas por código o nombre."""
        term = termino.strip().lower()
        return [
            c for c in self.cuentas_ordenadas
            if term == c.codigo.lower() or term in c.nombre.lower()
        ]
