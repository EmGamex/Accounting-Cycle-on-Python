"""Excepciones especializadas para el módulo de Balance de Comprobación y Situación General."""


class BalanceError(Exception):
    """Excepción base para errores del módulo de Balance."""
    pass


class BalanceVacioError(BalanceError):
    """Se levanta cuando se intenta generar un balance sin cuentas o movimientos registrados."""
    pass


class DescuadreBalanceError(BalanceError):
    """Se levanta cuando el balance de 4 columnas no cumple con la partida doble en sumas o saldos."""
    pass


class EcuacionPatrimonialError(BalanceError):
    """Se levanta cuando el Balance de Situación General no cumple con Activo = Pasivo + Patrimonio."""
    pass
