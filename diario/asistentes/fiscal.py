"""Asistente interactivo para la regularización y liquidación del IVA."""
from datetime import date
from decimal import Decimal
from typing import Optional

from rich.panel import Panel
from rich.table import Table

from config import CERO_MONETARIO, FORMATO_FECHA
from diario.engine import GestorLibroDiario
from diario.models import PartidaDiario
from diario.operaciones import (
    COD_IVA_CREDITO,
    COD_IVA_DEBITO,
    NOMBRE_IVA_CREDITO,
    NOMBRE_IVA_DEBITO,
    TIPO_RESULTADO_CERO,
    TIPO_RESULTADO_FAVOR,
    TIPO_RESULTADO_PAGAR,
    calcular_regularizacion_iva,
    crear_partida_regularizacion_iva,
)
from diario.prompts import pedir_fecha
from ui import (
    BORDE_PANEL,
    BORDE_TABLA,
    COLOR_AVISO,
    COLOR_ERROR,
    COLOR_EXITO,
    COLOR_PRIMARIO,
    COLOR_SECUNDARIO,
    COLOR_TEXTO,
    console,
    formatear_moneda,
    imprimir_alerta,
    imprimir_aviso,
    imprimir_banner,
    pedir_confirmacion,
)
from .comun import guardar_y_mostrar_partida


def _mostrar_resumen_iva(
    saldo_credito: Decimal,
    saldo_debito: Decimal,
    monto_compensar: Decimal,
    diferencia: Decimal,
    tipo: str,
) -> None:
    """Muestra una tabla con el desglose del IVA antes del asiento."""
    tabla = Table(
        title="Posición Tributaria del IVA (Guatemala)",
        box=BORDE_TABLA,
        border_style=COLOR_SECUNDARIO,
    )
    tabla.add_column("Cuenta Contable", style=COLOR_TEXTO)
    tabla.add_column("Código", justify="center", style="dim cyan")
    tabla.add_column("Saldo Acumulado", justify="right", style=COLOR_EXITO)

    tabla.add_row(
        f"{NOMBRE_IVA_CREDITO} (Compras / Gastos)",
        COD_IVA_CREDITO,
        formatear_moneda(saldo_credito),
    )
    tabla.add_row(
        f"{NOMBRE_IVA_DEBITO} (Ventas)",
        COD_IVA_DEBITO,
        formatear_moneda(saldo_debito),
    )
    tabla.add_section()
    tabla.add_row(
        f"[{COLOR_PRIMARIO}]Monto a Compensar / Regularizar[/{COLOR_PRIMARIO}]",
        "—",
        f"[{COLOR_PRIMARIO}]{formatear_moneda(monto_compensar)}[/{COLOR_PRIMARIO}]",
    )

    console.print(tabla)

    if tipo == TIPO_RESULTADO_PAGAR:
        detalle = (
            f"[{COLOR_AVISO}]Efecto:[/{COLOR_AVISO}] {NOMBRE_IVA_CREDITO} queda saldado en {formatear_moneda(CERO_MONETARIO)}.\n"
            f"Impuesto neto por pagar a la SAT (SAT-2237): [{COLOR_ERROR}]{formatear_moneda(diferencia)}[/{COLOR_ERROR}]"
        )
    elif tipo == TIPO_RESULTADO_FAVOR:
        detalle = (
            f"[{COLOR_AVISO}]Efecto:[/{COLOR_AVISO}] {NOMBRE_IVA_DEBITO} queda saldado en {formatear_moneda(CERO_MONETARIO)}.\n"
            f"Remanente de Crédito Fiscal a favor para el siguiente período: [{COLOR_EXITO}]{formatear_moneda(diferencia)}[/{COLOR_EXITO}]"
        )
    else:
        detalle = f"[{COLOR_EXITO}]Efecto:[/{COLOR_EXITO}] Ambas cuentas de IVA quedan completamente saldadas en {formatear_moneda(CERO_MONETARIO)}."

    console.print(Panel(detalle, box=BORDE_PANEL, border_style=COLOR_SECUNDARIO, title="Resultado del Ajuste"))


def regularizar_iva_asistido(
    gestor: GestorLibroDiario,
    fecha_sugerida: Optional[date] = None,
) -> Optional[PartidaDiario]:
    """Guía al usuario para revisar saldos de IVA y asentar la partida de regularización."""
    imprimir_banner("REGULARIZACIÓN Y LIQUIDACIÓN DEL IVA", border_style=COLOR_SECUNDARIO)

    saldo_credito, saldo_debito = gestor.obtener_saldos_iva()

    if saldo_credito <= CERO_MONETARIO and saldo_debito <= CERO_MONETARIO:
        imprimir_alerta(
            f"No se registran movimientos ni saldos en {NOMBRE_IVA_CREDITO} ({COD_IVA_CREDITO}) "
            f"ni en {NOMBRE_IVA_DEBITO} ({COD_IVA_DEBITO})."
        )
        return None

    if saldo_credito <= CERO_MONETARIO or saldo_debito <= CERO_MONETARIO:
        imprimir_aviso(
            f"No procede regularización por compensación:\n"
            f" • {NOMBRE_IVA_CREDITO} ({COD_IVA_CREDITO}): {formatear_moneda(saldo_credito)}\n"
            f" • {NOMBRE_IVA_DEBITO} ({COD_IVA_DEBITO}):  {formatear_moneda(saldo_debito)}\n"
            f"Solo una de las cuentas tiene saldo, por lo que no existe monto compensable mutuo."
        )
        return None

    monto_compensar, diferencia, tipo = calcular_regularizacion_iva(saldo_credito, saldo_debito)

    _mostrar_resumen_iva(saldo_credito, saldo_debito, monto_compensar, diferencia, tipo)

    if not pedir_confirmacion("¿Deseas asentar la partida de Regularización de IVA en el Libro Diario?", default=True):
        imprimir_aviso("Operación cancelada por el usuario.")
        return None

    # Determinación de fecha por defecto (última partida del libro o fecha actual)
    if fecha_sugerida is None:
        partidas = gestor.obtener_partidas()
        fecha_sugerida = partidas[-1].fecha if partidas else date.today()

    console.print(f"Fecha del asiento (default: {fecha_sugerida.strftime(FORMATO_FECHA)}):")
    fecha = pedir_fecha()

    partida = crear_partida_regularizacion_iva(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        monto=monto_compensar,
    )

    return guardar_y_mostrar_partida(
        gestor,
        partida,
        f"[{COLOR_EXITO}]Partida de Regularización de IVA asentada exitosamente[/{COLOR_EXITO}]",
    )
