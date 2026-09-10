"""Módulo central del Libro Diario del Sistema Contable Integral."""
from .conectores import de_partida_apertura, de_partida_planilla
from .engine import GestorLibroDiario
from .exceptions import (
    CorrelativoError,
    CuentaInvalidaError,
    DescuadrePartidaError,
    DiarioError,
    FechaInvalidaError,
)
from .models import (
    LibroDiario,
    MovimientoLinea,
    PartidaDiario,
    TipoOrigenPartida,
)
from .operaciones import (
    crear_partida_abono_cliente,
    crear_partida_abono_prestamo,
    crear_partida_abono_proveedor,
    crear_partida_compra,
    crear_partida_deposito_banco,
    crear_partida_retiro_banco,
    crear_partida_simple,
    crear_partida_venta,
)
from .cli import iniciar_flujo_diario
from .reportes import (
    generar_texto_libro_diario,
    generar_texto_partida,
)

__all__ = [
    "iniciar_flujo_diario",
    "CorrelativoError",
    "CuentaInvalidaError",
    "DescuadrePartidaError",
    "DiarioError",
    "FechaInvalidaError",
    "GestorLibroDiario",
    "LibroDiario",
    "MovimientoLinea",
    "PartidaDiario",
    "TipoOrigenPartida",
    "crear_partida_abono_cliente",
    "crear_partida_abono_prestamo",
    "crear_partida_abono_proveedor",
    "crear_partida_compra",
    "crear_partida_deposito_banco",
    "crear_partida_retiro_banco",
    "crear_partida_simple",
    "crear_partida_venta",
    "de_partida_apertura",
    "de_partida_planilla",
    "generar_texto_libro_diario",
    "generar_texto_partida",
]
