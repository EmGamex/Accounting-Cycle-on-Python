"""Punto de entrada principal y unificado para el Sistema Contable Integral (Guatemala)."""
import sys
from typing import Optional

from apertura.cli import iniciar_flujo_apertura
from planilla.cli import iniciar_flujo_planillas
from diario.cli import iniciar_flujo_diario
from mayor.cli import iniciar_flujo_mayor
from diario.engine import GestorLibroDiario

import orquestador
from orquestador import ARCHIVO_EJERCICIO_DEFAULT


def menu_persistencia(gestor: GestorLibroDiario) -> None:
    """Submenú de persistencia con sincronización de entorno."""
    this_module = sys.modules[__name__]
    orquestador.ARCHIVO_EJERCICIO_DEFAULT = getattr(
        this_module, "ARCHIVO_EJERCICIO_DEFAULT", orquestador.ARCHIVO_EJERCICIO_DEFAULT
    )
    orquestador._menu_persistencia_core(gestor)


def menu_principal(gestor: Optional[GestorLibroDiario] = None) -> None:
    """Delegador interactivo que invoca la capa de orquestación contable."""
    this_module = sys.modules[__name__]
    orquestador.iniciar_flujo_apertura = getattr(this_module, "iniciar_flujo_apertura", orquestador.iniciar_flujo_apertura)
    orquestador.iniciar_flujo_planillas = getattr(this_module, "iniciar_flujo_planillas", orquestador.iniciar_flujo_planillas)
    orquestador.iniciar_flujo_diario = getattr(this_module, "iniciar_flujo_diario", orquestador.iniciar_flujo_diario)
    orquestador.iniciar_flujo_mayor = getattr(this_module, "iniciar_flujo_mayor", orquestador.iniciar_flujo_mayor)
    orquestador.menu_persistencia = getattr(this_module, "menu_persistencia", orquestador.menu_persistencia)
    orquestador.ARCHIVO_EJERCICIO_DEFAULT = getattr(this_module, "ARCHIVO_EJERCICIO_DEFAULT", orquestador.ARCHIVO_EJERCICIO_DEFAULT)

    orquestador.menu_principal(gestor=gestor)


def main() -> None:
    """Función de arranque principal del sistema con cierre limpio."""
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\nSesión finalizada por el usuario. Saliendo...")
        sys.exit(0)


if __name__ == "__main__":
    main()