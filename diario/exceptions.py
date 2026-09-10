"""Excepciones especializadas para el módulo de Libro Diario."""


class DiarioError(Exception):
    """Excepción base para errores del módulo de Libro Diario."""
    pass


class DescuadrePartidaError(DiarioError):
    """Se levanta cuando la suma del Debe no es exactamente igual a la del Haber."""
    pass


class CorrelativoError(DiarioError):
    """Se levanta cuando el número de partida rompe la correlatividad estricta."""
    pass


class CuentaInvalidaError(DiarioError):
    """Se levanta cuando una cuenta no existe o no es válida en el catálogo contable."""
    pass


class FechaInvalidaError(DiarioError):
    """Se levanta cuando la fecha de la partida presenta inconsistencias cronológicas."""
    pass
