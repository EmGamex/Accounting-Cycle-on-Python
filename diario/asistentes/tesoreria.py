"""Asistente de operaciones frecuentes (tesorería, cobros, pagos, depósitos y préstamos)."""
from dataclasses import dataclass
from typing import Callable, Optional

from diario.engine import GestorLibroDiario
from diario.models import PartidaDiario
from diario.operaciones import (
    crear_partida_abono_cliente,
    crear_partida_abono_prestamo,
    crear_partida_abono_proveedor,
    crear_partida_deposito_banco,
    crear_partida_retiro_banco,
    crear_partida_simple,
)
from diario.prompts import buscar_o_seleccionar_cuenta, pedir_fecha, pedir_monto

from .comun import COD_BANCOS, COD_CAJA, guardar_y_mostrar_partida


def _crear_abono_cliente(gestor: GestorLibroDiario) -> PartidaDiario:
    monto = pedir_monto("  Monto abonado por el cliente: Q ")
    medio = input("  ¿Cobrado en Efectivo [E] o Banco/Transferencia/Cheque [B]? (Default [E]): ").strip().upper() or "E"
    doc = input("  No. de Recibo / Documento de soporte (opcional): ").strip() or None
    fecha = pedir_fecha()
    canal = "banco" if medio == "B" else "caja"
    return crear_partida_abono_cliente(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        monto=monto,
        medio=canal,
        documento_soporte=doc,
    )


def _crear_abono_proveedor(gestor: GestorLibroDiario) -> PartidaDiario:
    monto = pedir_monto("  Monto a pagar al proveedor: Q ")
    medio = input("  ¿Pagado con Cheque/Transferencia [B] o Efectivo [E]? (Default [B]): ").strip().upper() or "B"
    doc = input("  No. de Cheque / Transferencia (ej. Ch. 4501): ").strip() or None
    fecha = pedir_fecha()
    canal = "caja" if medio == "E" else "banco"
    return crear_partida_abono_proveedor(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        monto=monto,
        medio=canal,
        documento_soporte=doc,
    )


def _crear_deposito_banco(gestor: GestorLibroDiario) -> PartidaDiario:
    monto = pedir_monto("  Monto a depositar en el Banco: Q ")
    doc = input("  No. de Boleta de Depósito (opcional): ").strip() or None
    fecha = pedir_fecha()
    return crear_partida_deposito_banco(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        monto=monto,
        documento_soporte=doc,
    )


def _crear_retiro_banco(gestor: GestorLibroDiario) -> PartidaDiario:
    monto = pedir_monto("  Monto retirado del Banco para Caja: Q ")
    doc = input("  No. de Cheque / Comprobante (opcional): ").strip() or None
    fecha = pedir_fecha()
    return crear_partida_retiro_banco(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        monto=monto,
        documento_soporte=doc,
    )


def _crear_abono_prestamo(gestor: GestorLibroDiario) -> PartidaDiario:
    monto = pedir_monto("  Monto del abono / amortización al préstamo: Q ")
    doc = input("  No. de Transferencia / Comprobante (opcional): ").strip() or None
    fecha = pedir_fecha()
    return crear_partida_abono_prestamo(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        monto=monto,
        documento_soporte=doc,
    )


def _crear_operacion_libre(gestor: GestorLibroDiario) -> PartidaDiario:
    glosa = input("  Descripción de la operación: ").strip() or "Operación simple"
    monto = pedir_monto("  Monto total de la operación: Q ")
    cod_debe, nom_debe = buscar_o_seleccionar_cuenta(
        "  Cuenta que recibe el cargo (DEBE)",
        default_codigo=COD_BANCOS,
        gestor=gestor,
    )
    cod_haber, nom_haber = buscar_o_seleccionar_cuenta(
        "  Cuenta que entrega el abono (HABER)",
        default_codigo=COD_CAJA,
        gestor=gestor,
    )
    doc = input("  Documento de soporte (opcional): ").strip() or None
    fecha = pedir_fecha()
    return crear_partida_simple(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        glosa=glosa,
        monto=monto,
        codigo_debe=cod_debe,
        nombre_debe=nom_debe,
        codigo_haber=cod_haber,
        nombre_haber=nom_haber,
        documento_soporte=doc,
    )


@dataclass(frozen=True)
class OpcionOperacionSimple:
    descripcion: str
    generador: Callable[[GestorLibroDiario], PartidaDiario]


OPERACIONES_SIMPLES_MAP = {
    "1": OpcionOperacionSimple("Abono / Cobro de Clientes (Clientes nos pagan)", _crear_abono_cliente),
    "2": OpcionOperacionSimple("Abono / Pago a Proveedores (Pagamos deuda con cheque o efectivo)", _crear_abono_proveedor),
    "3": OpcionOperacionSimple("Depósito en el Banco (Traslado de Caja a Bancos)", _crear_deposito_banco),
    "4": OpcionOperacionSimple("Retiro del Banco a Caja (Efectivo disponible)", _crear_retiro_banco),
    "5": OpcionOperacionSimple("Abono / Pago a Préstamo Bancario (Amortización de deuda)", _crear_abono_prestamo),
    "6": OpcionOperacionSimple("Otra operación libre (Elegir cuentas Debe y Haber a medida)", _crear_operacion_libre),
}


def registrar_operacion_simple_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Asistente de operaciones frecuentes usando tabla de despacho."""
    print("\n" + "=" * 65)
    print("      REGISTRO DE OPERACIONES FRECUENTES (PAGOS Y COBROS)")
    print("=" * 65)
    print("  Seleccione el tipo de operación:")
    for clave, item in OPERACIONES_SIMPLES_MAP.items():
        print(f"    [{clave}] {item.descripcion}")

    tipo = input("\n  Seleccione una opción [1-6] (Default [1]): ").strip() or "1"
    opcion = OPERACIONES_SIMPLES_MAP.get(tipo, OPERACIONES_SIMPLES_MAP["6"])
    partida = opcion.generador(gestor)
    return guardar_y_mostrar_partida(gestor, partida)
