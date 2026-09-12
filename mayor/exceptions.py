"""Excepciones especializadas para el módulo de Libro Mayor."""


class MayorError(Exception):
    """Excepción base para errores del módulo de Libro Mayor."""
    pass


class LibroDiarioVacioError(MayorError):
    """Se levanta cuando se intenta mayorizar un libro diario sin partidas registradas."""
    pass


class DescuadreMayorError(MayorError):
    """Se levanta cuando el libro diario de entrada está descuadrado o el mayor no cuadra."""
    pass


class CuentaNoEncontradaError(MayorError):
    """Se levanta cuando se intenta consultar una cuenta que no tiene movimientos en el mayor."""
    pass
