"""Modelos de datos fuertemente tipados para el Balance de 4 Columnas y Balance de Situación General."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

TWO_PLACES = Decimal("0.01")


@dataclass
class FilaBalance4Columnas:
    """Representa una fila formal de la matriz del Balance de Comprobación y Saldos."""
    numero: int
    codigo: str
    nombre: str
    suma_debe: Decimal = Decimal("0.00")
    suma_haber: Decimal = Decimal("0.00")
    saldo_deudor: Decimal = Decimal("0.00")
    saldo_acreedor: Decimal = Decimal("0.00")
    clase: str = ""
    subgrupo: str = ""
    es_regularizadora: bool = False
    es_saldo_anomalo: bool = False

    def __post_init__(self):
        if not isinstance(self.suma_debe, Decimal):
            self.suma_debe = Decimal(str(self.suma_debe))
        if not isinstance(self.suma_haber, Decimal):
            self.suma_haber = Decimal(str(self.suma_haber))
        if not isinstance(self.saldo_deudor, Decimal):
            self.saldo_deudor = Decimal(str(self.saldo_deudor))
        if not isinstance(self.saldo_acreedor, Decimal):
            self.saldo_acreedor = Decimal(str(self.saldo_acreedor))

        self.suma_debe = self.suma_debe.quantize(TWO_PLACES)
        self.suma_haber = self.suma_haber.quantize(TWO_PLACES)
        self.saldo_deudor = self.saldo_deudor.quantize(TWO_PLACES)
        self.saldo_acreedor = self.saldo_acreedor.quantize(TWO_PLACES)


@dataclass
class Balance4Columnas:
    """Matriz completa de Balance de Comprobación y Saldos (4 Columnas)."""
    empresa: str = "Empresa Ejemplo, S.A."
    periodo: str = "2026"
    fecha_emision: date = field(default_factory=date.today)
    filas: List[FilaBalance4Columnas] = field(default_factory=list)

    @property
    def total_debe(self) -> Decimal:
        """Suma de la Columna 1: Sumas Debe."""
        return sum((f.suma_debe for f in self.filas), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def total_haber(self) -> Decimal:
        """Suma de la Columna 2: Sumas Haber."""
        return sum((f.suma_haber for f in self.filas), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def total_saldos_deudores(self) -> Decimal:
        """Suma de la Columna 3: Saldos Deudores."""
        return sum((f.saldo_deudor for f in self.filas), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def total_saldos_acreedores(self) -> Decimal:
        """Suma de la Columna 4: Saldos Acreedores."""
        return sum((f.saldo_acreedor for f in self.filas), Decimal("0.00")).quantize(TWO_PLACES)

    @property
    def cuadran_sumas(self) -> bool:
        """Verifica igualdad matemática entre Sumas Debe y Sumas Haber."""
        return self.total_debe == self.total_haber

    @property
    def cuadran_saldos(self) -> bool:
        """Verifica igualdad matemática entre Saldos Deudores y Saldos Acreedores."""
        return self.total_saldos_deudores == self.total_saldos_acreedores

    @property
    def cuadra(self) -> bool:
        """Verifica la doble condición de cuadre reglamentaria."""
        return self.cuadran_sumas and self.cuadran_saldos

    @property
    def diferencia_sumas(self) -> Decimal:
        """Diferencia absoluta entre Sumas Debe y Sumas Haber."""
        return abs(self.total_debe - self.total_haber).quantize(TWO_PLACES)

    @property
    def diferencia_saldos(self) -> Decimal:
        """Diferencia absoluta entre Saldos Deudores y Saldos Acreedores."""
        return abs(self.total_saldos_deudores - self.total_saldos_acreedores).quantize(TWO_PLACES)

    def obtener_fila(self, codigo: str) -> Optional[FilaBalance4Columnas]:
        """Obtiene una fila por su código contable."""
        cod_clean = codigo.strip()
        for f in self.filas:
            if f.codigo == cod_clean:
                return f
        return None

    def filtrar_por_clase(self, prefijo_clase: str) -> List[FilaBalance4Columnas]:
        """Filtra filas según el prefijo de su código (ej. '1' Activo, '2' Pasivo, etc.)."""
        pref = prefijo_clase.strip()
        return [f for f in self.filas if f.codigo.startswith(pref)]


@dataclass
class ResumenResultados:
    """Resumen de pérdidas y ganancias obtenido de las cuentas nominales (Clases 4 y 5)."""
    total_ingresos: Decimal = Decimal("0.00")
    total_costos: Decimal = Decimal("0.00")
    total_gastos: Decimal = Decimal("0.00")
    resultado_ejercicio: Decimal = Decimal("0.00")
    es_ganancia: bool = True

    def __post_init__(self):
        if not isinstance(self.total_ingresos, Decimal):
            self.total_ingresos = Decimal(str(self.total_ingresos))
        if not isinstance(self.total_costos, Decimal):
            self.total_costos = Decimal(str(self.total_costos))
        if not isinstance(self.total_gastos, Decimal):
            self.total_gastos = Decimal(str(self.total_gastos))
        if not isinstance(self.resultado_ejercicio, Decimal):
            self.resultado_ejercicio = Decimal(str(self.resultado_ejercicio))

        self.total_ingresos = self.total_ingresos.quantize(TWO_PLACES)
        self.total_costos = self.total_costos.quantize(TWO_PLACES)
        self.total_gastos = self.total_gastos.quantize(TWO_PLACES)
        self.resultado_ejercicio = self.resultado_ejercicio.quantize(TWO_PLACES)


@dataclass
class ItemBalanceGeneral:
    """Elemento individual de cuenta en el Balance de Situación General de Cierre."""
    codigo: str
    nombre: str
    monto: Decimal
    es_regularizadora: bool = False

    def __post_init__(self):
        if not isinstance(self.monto, Decimal):
            self.monto = Decimal(str(self.monto))
        self.monto = self.monto.quantize(TWO_PLACES)


@dataclass
class BalanceSituacionGeneral:
    """Balance de Situación General de Cierre clasificado conforme a NIIF y legislación guatemalteca."""
    empresa: str = "Empresa Ejemplo, S.A."
    periodo: str = "2026"
    fecha_emision: date = field(default_factory=date.today)
    total_activo_corriente: Decimal = Decimal("0.00")
    total_activo_no_corriente: Decimal = Decimal("0.00")
    total_activo: Decimal = Decimal("0.00")
    total_pasivo_corriente: Decimal = Decimal("0.00")
    total_pasivo_no_corriente: Decimal = Decimal("0.00")
    total_pasivo: Decimal = Decimal("0.00")
    patrimonio_capital: Decimal = Decimal("0.00")
    patrimonio_reservas: Decimal = Decimal("0.00")
    patrimonio_resultados_acumulados: Decimal = Decimal("0.00")
    resultado_ejercicio: Decimal = Decimal("0.00")
    total_patrimonio: Decimal = Decimal("0.00")
    estructura: Dict[str, Dict[str, List[ItemBalanceGeneral]]] = field(default_factory=dict)
    resumen_resultados: Optional[ResumenResultados] = None

    def __post_init__(self):
        self.total_activo_corriente = self.total_activo_corriente.quantize(TWO_PLACES)
        self.total_activo_no_corriente = self.total_activo_no_corriente.quantize(TWO_PLACES)
        self.total_activo = self.total_activo.quantize(TWO_PLACES)
        self.total_pasivo_corriente = self.total_pasivo_corriente.quantize(TWO_PLACES)
        self.total_pasivo_no_corriente = self.total_pasivo_no_corriente.quantize(TWO_PLACES)
        self.total_pasivo = self.total_pasivo.quantize(TWO_PLACES)
        self.patrimonio_capital = self.patrimonio_capital.quantize(TWO_PLACES)
        self.patrimonio_reservas = self.patrimonio_reservas.quantize(TWO_PLACES)
        self.patrimonio_resultados_acumulados = self.patrimonio_resultados_acumulados.quantize(TWO_PLACES)
        self.resultado_ejercicio = self.resultado_ejercicio.quantize(TWO_PLACES)
        self.total_patrimonio = self.total_patrimonio.quantize(TWO_PLACES)

    @property
    def total_pasivo_y_patrimonio(self) -> Decimal:
        """Suma de Pasivo y Patrimonio Neto."""
        return (self.total_pasivo + self.total_patrimonio).quantize(TWO_PLACES)

    @property
    def cuadra(self) -> bool:
        """Verifica la Ecuación Fundamental: Activo == Pasivo + Patrimonio Neto."""
        return self.total_activo == self.total_pasivo_y_patrimonio

    @property
    def diferencia(self) -> Decimal:
        """Diferencia absoluta de la Ecuación Patrimonial."""
        return abs(self.total_activo - self.total_pasivo_y_patrimonio).quantize(TWO_PLACES)
