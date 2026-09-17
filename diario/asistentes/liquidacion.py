"""Módulo desacoplado para la captura y cálculo de condiciones de liquidación y tratamiento de IVA."""
from decimal import Decimal
from typing import NamedTuple, Optional, Tuple

from config import PRECISION_CENTAVOS
from diario.operaciones.calculos import calcular_desglose_iva, calcular_iva_desde_base
from diario.prompts import pedir_monto
from ui import console, imprimir_alerta, imprimir_aviso

CIEN = Decimal("100.00")
UNO = Decimal("1.00")
CERO = Decimal("0.00")


class DetalleLiquidacion(NamedTuple):
    """Porcentajes o montos de liquidación para una compra o venta comercial."""
    pct_efectivo: Decimal = CERO
    pct_banco: Decimal = CERO
    pct_credito: Decimal = CERO
    pct_documentos: Decimal = CERO
    monto_efectivo: Optional[Decimal] = None
    monto_banco: Optional[Decimal] = None
    monto_credito: Optional[Decimal] = None
    monto_documentos: Optional[Decimal] = None


def pedir_tipo_ingreso_iva(etiqueta_operacion: str) -> Tuple[Decimal, Decimal, Decimal]:
    """Pregunta si el importe base tiene IVA incluido o es 'Más IVA'.

    Retorna tupla: (base_neta, iva, total_factura)
    """
    console.print(f"\n  [bold]Modalidad del importe de la {etiqueta_operacion}:[/bold]")
    console.print("    [1] Con IVA incluido (Total de factura final)")
    console.print("    [2] Más IVA (Valor neto + 12% Débito/Crédito Fiscal)")
    modalidad = input("  Seleccione [1-2] (Default [1]): ").strip() or "1"

    if modalidad == "2":
        neto = pedir_monto(f"Valor neto de la {etiqueta_operacion} (sin IVA): Q ")
        base, iva, total = calcular_iva_desde_base(neto)
        console.print(f"    -> Base: [cyan]Q {base:,.2f}[/cyan] | IVA (12%): [cyan]Q {iva:,.2f}[/cyan] | Total: [bold green]Q {total:,.2f}[/bold green]")
        return base, iva, total

    total = pedir_monto(f"Total de la {etiqueta_operacion} (con IVA incluido): Q ")
    base, iva = calcular_desglose_iva(total)
    console.print(f"    -> Base: [cyan]Q {base:,.2f}[/cyan] | IVA (12%): [cyan]Q {iva:,.2f}[/cyan] | Total: [bold green]Q {total:,.2f}[/bold green]")
    return base, iva, total


def capturar_liquidacion_multicanal(
    etiqueta_tipo: str,
    etiqueta_credito: str,
    pct_banco_mixto_default: str = "20",
) -> DetalleLiquidacion:
    """Captura interactiva flexible para formas de liquidación (Contado, Crédito, Mixto Simple, Multicanal/Letras)."""
    etiqueta_docs = "Documentos por Pagar (Letras)" if "pago" in etiqueta_tipo.lower() else "Documentos por Cobrar (Letras)"

    console.print(f"\n  [bold]Condición de {etiqueta_tipo}:[/bold]")
    console.print("    [1] 100% Contado (Bancos o Caja)")
    console.print(f"    [2] 100% Crédito ({etiqueta_credito})")
    console.print("    [3] Mixto Estándar (Transferencia Bancaria + Saldo a Crédito)")
    console.print(f"    [4] Mixto Personalizado / Letras de Cambio (Cheques, Efectivo, Crédito y {etiqueta_docs})")

    cond = input("  Seleccione [1-4] (Default [1]): ").strip() or "1"

    if cond == "2":
        return DetalleLiquidacion(pct_credito=UNO)

    if cond == "3":
        pct_in = (
            input(f"    % a liquidar por Banco/Transferencia (ej. {pct_banco_mixto_default}): ").strip()
            or pct_banco_mixto_default
        )
        try:
            pct_banco = Decimal(pct_in) / CIEN
            pct_credito = UNO - pct_banco
        except Exception:
            pct_banco = Decimal("0.20")
            pct_credito = Decimal("0.80")
        console.print(f"    -> Se asignará {pct_banco * 100:.1f}% a Bancos y {pct_credito * 100:.1f}% a {etiqueta_credito}.")
        return DetalleLiquidacion(pct_banco=pct_banco, pct_credito=pct_credito)

    if cond == "4":
        console.print("\n    [dim]Ingrese los porcentajes para cada canal (el remanente se puede asignar automáticamente):[/dim]")
        
        def pedir_pct_canal(nombre_canal: str) -> Decimal:
            val = input(f"      % para {nombre_canal} [0-100, Enter para 0]: ").strip()
            if not val:
                return CERO
            try:
                num = Decimal(val)
                return (num / CIEN) if num > UNO else num
            except Exception:
                return CERO

        pct_banco = pedir_pct_canal("Bancos / Cheque / Transferencia")
        pct_efectivo = pedir_pct_canal("Caja / Efectivo")
        pct_credito = pedir_pct_canal(f"Crédito ({etiqueta_credito})")
        pct_docs = pedir_pct_canal(f"{etiqueta_docs}")

        total_pct = pct_banco + pct_efectivo + pct_credito + pct_docs

        if total_pct == CERO:
            imprimir_aviso("    No se ingresaron porcentajes. Se asume 100% Contado vía Bancos.")
            return DetalleLiquidacion(pct_banco=UNO)

        if total_pct != UNO:
            console.print(f"    [dim]-> Suma de porcentajes: {total_pct * 100:.1f}%. El sistema normalizará la proporción de cada canal.[/dim]")

        return DetalleLiquidacion(
            pct_efectivo=pct_efectivo,
            pct_banco=pct_banco,
            pct_credito=pct_credito,
            pct_documentos=pct_docs,
        )

    # Caso 1: 100% Contado
    medio = input(f"    ¿{etiqueta_tipo.capitalize()} con Bancos/Cheque [B] o Caja/Efectivo [C]? (Default [B]): ").strip().upper() or "B"
    if medio == "C":
        return DetalleLiquidacion(pct_efectivo=UNO)
    return DetalleLiquidacion(pct_banco=UNO)
