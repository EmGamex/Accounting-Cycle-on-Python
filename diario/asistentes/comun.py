"""Constantes, modelos y funciones auxiliares compartidas por los asistentes."""
from decimal import Decimal
from typing import NamedTuple, Optional

from catalogo_contable import Cuenta
from diario.engine import GestorLibroDiario
from diario.exceptions import DescuadrePartidaError
from diario.models import PartidaDiario
from diario.reportes import generar_texto_partida

# ---------------------------------------------------------------------------
# CONSTANTES: Cuentas contables canónicas importadas del catálogo central
# ---------------------------------------------------------------------------
COD_CAJA = Cuenta.CAJA
COD_BANCOS = Cuenta.BANCOS
COD_MERCADERIAS = Cuenta.MERCADERIAS
COD_MOBILIARIO = Cuenta.MOBILIARIO
COD_PROVEEDORES = Cuenta.PROVEEDORES
COD_CAPITAL = Cuenta.CAPITAL_SOCIAL
COD_GASTO_DEFAULT = Cuenta.GASTOS_ADMIN

CIEN = Decimal("100.00")
UNO = Decimal("1.00")
CERO = Decimal("0.00")


class DistribucionPago(NamedTuple):
    """Porcentajes de liquidación calculados para una compra o venta."""
    pct_efectivo: Decimal = CERO
    pct_banco: Decimal = CERO
    pct_credito: Decimal = CERO


def guardar_y_mostrar_partida(
    gestor: GestorLibroDiario,
    partida: PartidaDiario,
    mensaje_exito: str = "Partida registrada exitosamente",
) -> Optional[PartidaDiario]:
    """Registra la partida en el gestor y reporta el resultado en consola."""
    try:
        gestor.registrar_partida(partida)
        print(f"\n  [OK] {mensaje_exito}:")
        print(generar_texto_partida(partida))
        return partida
    except DescuadrePartidaError as e:
        print(f"\n  [ERROR DE CUADRE] {e}")
        print("  La partida no se registró porque violaría el principio de partida doble.")
        return None
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")
        return None


def capturar_condicion_liquidacion(
    etiqueta_tipo: str,
    etiqueta_credito: str,
    pct_banco_mixto_default: str = "20",
) -> DistribucionPago:
    """Captura y calcula los porcentajes para operaciones de Contado, Crédito o Mixto."""
    print(f"\n  Condición de {etiqueta_tipo}:")
    print("    [1] 100% Contado (Bancos o Caja)")
    print(f"    [2] 100% Crédito ({etiqueta_credito})")
    print("    [3] Mixto (ej. Transferencia Bancaria + Saldo a Crédito)")
    cond = input("  Seleccione [1-3] (Default [1]): ").strip() or "1"

    if cond == "2":
        return DistribucionPago(pct_credito=UNO)

    if cond == "3":
        pct_in = input(
            f"    % a liquidar por Banco/Transferencia (ej. {pct_banco_mixto_default}): "
        ).strip() or pct_banco_mixto_default
        pct_banco = Decimal(pct_in) / CIEN
        pct_credito = UNO - pct_banco
        print(f"    -> Se asignará {pct_banco * 100:.1f}% a Bancos y {pct_credito * 100:.1f}% a {etiqueta_credito}.")
        return DistribucionPago(pct_banco=pct_banco, pct_credito=pct_credito)

    # Caso 1: 100% Contado
    medio = input(f"    ¿{etiqueta_tipo.capitalize()} con Bancos [B] o Caja/Efectivo [C]? (Default [B]): ").strip().upper() or "B"
    if medio == "C":
        return DistribucionPago(pct_efectivo=UNO)
    return DistribucionPago(pct_banco=UNO)
