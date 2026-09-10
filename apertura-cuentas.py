"""Punto de entrada principal para el sistema de apertura contable."""
import sys
from apertura import (
    CatalogoService,
    MotorApertura,
    iniciar_flujo_apertura,
    generar_texto_balance,
    generar_texto_partida,
    normalizar,
    es_cuenta_regularizadora,
)

# Compatibilidad con llamadas heredadas
main = iniciar_flujo_apertura

if __name__ == "__main__":
    try:
        iniciar_flujo_apertura()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario. Saliendo...")
        sys.exit(0)