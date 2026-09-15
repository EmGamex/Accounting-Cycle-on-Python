"""Validadores de consistencia contable y reglas de negocio para persistencia."""
from .exceptions import IntegridadDatosError


def validar_integridad_contable(libro) -> None:
    """Verifica que todas las partidas del libro diario cumplan con la partida doble."""
    for partida in libro.partidas:
        if not partida.cuadra:
            raise IntegridadDatosError(
                f"La Partida No. {partida.numero} del Libro Diario está descuadrada: "
                f"Debe={partida.total_debe}, Haber={partida.total_haber}, Diferencia={partida.diferencia}"
            )
