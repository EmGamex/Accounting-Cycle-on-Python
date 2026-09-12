"""Asistentes para operaciones comerciales con IVA (12%): Compras y Ventas."""
from typing import Optional

from diario.engine import GestorLibroDiario
from diario.models import PartidaDiario
from diario.operaciones import crear_partida_compra, crear_partida_venta
from diario.prompts import buscar_o_seleccionar_cuenta, pedir_fecha, pedir_monto

from ui import imprimir_banner
from .comun import COD_GASTO_DEFAULT, capturar_condicion_liquidacion, guardar_y_mostrar_partida


def registrar_compra_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Registra una compra con desglose automático de Crédito Fiscal IVA (12%)."""
    imprimir_banner("REGISTRO DE COMPRA O GASTO CON IVA (12%)", border_style="cyan")
    glosa = input("Descripción o concepto de la compra: ").strip() or "Compra de bienes/servicios para la empresa"
    doc = input("No. de Factura / Documento: ").strip() or "FAC-001"
    total = pedir_monto("Total de la factura (IVA incluido): Q ")

    cod_gasto, nom_gasto = buscar_o_seleccionar_cuenta(
        "Cuenta de gasto o activo",
        default_codigo=COD_GASTO_DEFAULT,
        gestor=gestor,
    )
    fecha = pedir_fecha()
    dist = capturar_condicion_liquidacion(
        etiqueta_tipo="pago",
        etiqueta_credito="Proveedores Locales",
        pct_banco_mixto_default="20",
    )

    partida = crear_partida_compra(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        glosa=glosa,
        total_factura=total,
        codigo_gasto=cod_gasto,
        nombre_gasto=nom_gasto,
        pct_efectivo=dist.pct_efectivo,
        pct_banco=dist.pct_banco,
        pct_proveedores=dist.pct_credito,
        documento_soporte=doc,
    )
    return guardar_y_mostrar_partida(gestor, partida, "Partida de compra registrada")


def registrar_venta_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Registra una venta con desglose automático de Débito Fiscal IVA (12%)."""
    imprimir_banner("REGISTRO DE VENTA CON IVA (12%)", border_style="cyan")
    glosa = input("Descripción o concepto de la venta: ").strip() or "Venta de mercaderías"
    doc = input("No. de Factura emitida (FEL): ").strip() or "FEL"
    total = pedir_monto("Total de la venta (IVA incluido): Q ")
    fecha = pedir_fecha()

    dist = capturar_condicion_liquidacion(
        etiqueta_tipo="cobro",
        etiqueta_credito="Cuentas por Cobrar Clientes",
        pct_banco_mixto_default="60",
    )

    partida = crear_partida_venta(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        glosa=glosa,
        total_factura=total,
        pct_efectivo=dist.pct_efectivo,
        pct_banco=dist.pct_banco,
        pct_credito=dist.pct_credito,
        documento_soporte=doc,
    )
    return guardar_y_mostrar_partida(gestor, partida, "Partida de venta registrada")
