"""Punto de entrada principal interactivo para el Libro Diario."""
import sys
from diario.cli import iniciar_flujo_diario

# Alias para compatibilidad con invocaciones programáticas existentes
main = iniciar_flujo_diario

if __name__ == "__main__":
    try:
        iniciar_flujo_diario()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario. Saliendo...")
        sys.exit(0)
