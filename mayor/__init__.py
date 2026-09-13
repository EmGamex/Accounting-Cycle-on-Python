"""Módulo de Libro Mayor y T-Gráficas del Sistema Contable Integral (Guatemala)."""
from .engine import GestorLibroMayor, mayorizar_libro_diario
from .exceptions import (
    CuentaNoEncontradaError,
    DescuadreMayorError,
    LibroDiarioVacioError,
    MayorError,
)
from .models import (
    CuentaMayor,
    LibroMayor,
    MovimientoMayor,
    NaturalezaSaldo,
)


def iniciar_flujo_mayor(*args, **kwargs):
    """Carga perezosa del flujo de CLI para evitar importaciones circulares."""
    from .cli import iniciar_flujo_mayor as _iniciar
    return _iniciar(*args, **kwargs)


__all__ = [
    "CuentaMayor",
    "CuentaNoEncontradaError",
    "DescuadreMayorError",
    "GestorLibroMayor",
    "LibroDiarioVacioError",
    "LibroMayor",
    "MayorError",
    "MovimientoMayor",
    "NaturalezaSaldo",
    "iniciar_flujo_mayor",
    "mayorizar_libro_diario",
]
