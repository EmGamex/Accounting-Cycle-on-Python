"""Punto de entrada principal para el Sistema Contable Integral (Guatemala)."""
import sys

from orquestador import menu_principal
from ui import console


def main() -> None:
    """Función de arranque principal del sistema con cierre limpio."""
    try:
        menu_principal()
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Sesión finalizada por el usuario. Saliendo...[/bold yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()