"""Asistentes interactivos de captura guiada de operaciones para el Libro Diario."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, NamedTuple, Optional, Tuple

from apertura import CatalogoService, MotorApertura, iniciar_flujo_apertura
from planilla import DatosEmpleado, calcular_boleta, generar_partida_contable
from diario.conectores import de_partida_apertura, de_partida_planilla
from diario.engine import GestorLibroDiario
from diario.exceptions import DescuadrePartidaError
from diario.models import PartidaDiario
from diario.operaciones import (
    crear_partida_abono_cliente,
    crear_partida_abono_prestamo,
    crear_partida_abono_proveedor,
    crear_partida_compra,
    crear_partida_deposito_banco,
    crear_partida_retiro_banco,
    crear_partida_simple,
    crear_partida_venta,
)
from diario.prompts import buscar_o_seleccionar_cuenta, pedir_fecha, pedir_monto
from diario.reportes import generar_texto_partida

# ---------------------------------------------------------------------------
# CONSTANTES: Cuentas y valores predeterminados
# ---------------------------------------------------------------------------
COD_CAJA = "1101"
COD_BANCOS = "1102"
COD_MERCADERIAS = "1104"
COD_MOBILIARIO = "1204"
COD_PROVEEDORES = "2101"
COD_CAPITAL = "3101"
COD_GASTO_DEFAULT = "5201"

CIEN = Decimal("100.00")
UNO = Decimal("1.00")
CERO = Decimal("0.00")

# Datos demo de saldos iniciales (Apertura)
DEMO_APERTURA_ITEMS: Tuple[Tuple[str, Decimal], ...] = (
    (COD_CAJA, Decimal("10000.00")),
    (COD_BANCOS, Decimal("45000.00")),
    (COD_MERCADERIAS, Decimal("30000.00")),
    (COD_MOBILIARIO, Decimal("15000.00")),
    (COD_PROVEEDORES, Decimal("20000.00")),
)

# Datos demo de nómina (Planilla)
DEMO_NOMINA_EMPLEADOS = (
    DatosEmpleado("Juan Morales", Decimal("5500.00"), departamento="Administración", horas_extras=Decimal("4.0")),
    DatosEmpleado("Ana Castillo", Decimal("4000.00"), departamento="Ventas", ventas=Decimal("35000.00"), pct_comision=Decimal("0.03")),
)


# ---------------------------------------------------------------------------
# HELPERS REUTILIZABLES
# ---------------------------------------------------------------------------
def _guardar_y_mostrar_partida(
    gestor: GestorLibroDiario,
    partida: PartidaDiario,
    mensaje_exito: str = "Partida registrada exitosamente",
) -> Optional[PartidaDiario]:
    """Registra la partida en el gestor y reporta el resultado al usuario."""
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


class DistribucionPago(NamedTuple):
    """Porcentajes de liquidación calculados para una compra o venta."""
    pct_efectivo: Decimal = CERO
    pct_banco: Decimal = CERO
    pct_credito: Decimal = CERO


def _capturar_condicion_liquidacion(
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
        pct_in = input(f"    % a liquidar por Banco/Transferencia (ej. {pct_banco_mixto_default}): ").strip() or pct_banco_mixto_default
        pct_banco = Decimal(pct_in) / CIEN
        pct_credito = UNO - pct_banco
        print(f"    -> Se asignará {pct_banco * 100:.1f}% a Bancos y {pct_credito * 100:.1f}% a {etiqueta_credito}.")
        return DistribucionPago(pct_banco=pct_banco, pct_credito=pct_credito)

    # Caso 1: 100% Contado
    medio = input(f"    ¿{etiqueta_tipo.capitalize()} con Bancos [B] o Caja/Efectivo [C]? (Default [B]): ").strip().upper() or "B"
    if medio == "C":
        return DistribucionPago(pct_efectivo=UNO)
    return DistribucionPago(pct_banco=UNO)


# ---------------------------------------------------------------------------
# ASISTENTES PRINCIPALES
# ---------------------------------------------------------------------------
def registrar_apertura_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Genera y registra la Partida #1 a partir de un balance inicial de apertura."""
    print("\n" + "=" * 65)
    print("      REGISTRO DE PARTIDA No. 1 - BALANCE DE APERTURA")
    print("=" * 65)
    print("  [1] Generar apertura con datos de ejemplo (Caja, Bancos, Mercaderías, Capital)")
    print("  [2] Ingresar saldos iniciales cuenta por cuenta")
    opcion = input("\nSeleccione [1]: ").strip() or "1"

    if opcion == "1":
        cat = CatalogoService.desde_modulo()
        motor_ap = MotorApertura()
        for cod, monto in DEMO_APERTURA_ITEMS:
            cta = cat.buscar(cod)
            if cta:
                motor_ap.agregar_o_acumular(cta, monto)
        res = motor_ap.calcular_balance()
        cta_capital = cat.buscar(COD_CAPITAL)
        if cta_capital:
            motor_ap.asignar_diferencia_capital(cta_capital, res.diferencia_capital)

        fecha = pedir_fecha("Fecha del asiento de apertura [Hoy]: ")
        pda_ap = motor_ap.generar_partida_apertura(numero=gestor.siguiente_numero)
    else:
        # Usa el flujo completo e interactivo de apertura-cuentas
        _, pda_ap = iniciar_flujo_apertura(
            numero_partida=gestor.siguiente_numero,
            exportar_archivo=False,
            imprimir_reportes=True,
        )
        if not pda_ap:
            print("\n  [!] Apertura cancelada o sin cuentas registradas.")
            return None
        fecha = pedir_fecha("\nFecha del asiento de apertura en el Libro Diario [Hoy]: ")

    partida_diario = de_partida_apertura(pda_ap, fecha=fecha, numero=gestor.siguiente_numero)
    return _guardar_y_mostrar_partida(gestor, partida_diario)


def registrar_nomina_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Genera y registra la partida de sueldos desde el módulo de planilla."""
    print("\n" + "=" * 65)
    print("           REGISTRO DE PARTIDA DE SUELDOS Y SALARIOS")
    print("=" * 65)
    print("  [1] Generar nómina de ejemplo (Administración y Ventas)")
    print("  [2] Ingresar empleado manualmente")
    opcion = input("\nSeleccione [1]: ").strip() or "1"

    if opcion == "1":
        resultados = [calcular_boleta(e) for e in DEMO_NOMINA_EMPLEADOS]
    else:
        nombre = input("Nombre del empleado: ").strip() or "Empleado 1"
        depto = input("Departamento (Administración/Ventas) [Administración]: ").strip() or "Administración"
        sueldo = pedir_monto("Sueldo Base: ")
        emp = DatosEmpleado(nombre=nombre, sueldo_base=sueldo, departamento=depto)
        resultados = [calcular_boleta(emp)]

    pda_contable = generar_partida_contable(resultados)
    fecha = pedir_fecha("Fecha de liquidación [Hoy]: ")
    partida_diario = de_partida_planilla(pda_contable, fecha=fecha, numero=gestor.siguiente_numero)
    return _guardar_y_mostrar_partida(gestor, partida_diario, "Partida de nómina registrada exitosamente")


def registrar_compra_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Registra una compra con desglose automático de Crédito Fiscal IVA (12%)."""
    print("\n" + "=" * 65)
    print("          REGISTRO DE COMPRA O GASTO CON IVA (12%)")
    print("=" * 65)
    glosa = input("Descripción o concepto de la compra: ").strip() or "Compra de bienes/servicios para la empresa"
    doc = input("No. de Factura / Documento: ").strip() or "FAC-001"
    total = pedir_monto("Total de la factura (IVA incluido): Q ")

    cod_gasto, nom_gasto = buscar_o_seleccionar_cuenta(
        "Cuenta de gasto o activo",
        default_codigo=COD_GASTO_DEFAULT,
        gestor=gestor,
    )
    fecha = pedir_fecha()
    dist = _capturar_condicion_liquidacion(
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
    return _guardar_y_mostrar_partida(gestor, partida, "Partida de compra registrada")


def registrar_venta_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Registra una venta con desglose automático de Débito Fiscal IVA (12%)."""
    print("\n" + "=" * 65)
    print("          REGISTRO DE VENTA CON IVA (12%)")
    print("=" * 65)
    glosa = input("Descripción o concepto de la venta: ").strip() or "Venta de mercaderías"
    doc = input("No. de Factura emitida (FEL): ").strip() or "FEL"
    total = pedir_monto("Total de la venta (IVA incluido): Q ")
    fecha = pedir_fecha()

    dist = _capturar_condicion_liquidacion(
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
    return _guardar_y_mostrar_partida(gestor, partida, "Partida de venta registrada")


# ---------------------------------------------------------------------------
# SUB-HANDLERS Y TABLA DE DESPACHO PARA OPERACIONES SIMPLES
# ---------------------------------------------------------------------------
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
    return _guardar_y_mostrar_partida(gestor, partida)


def registrar_partida_libre_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Permite armar un asiento contable línea por línea con validación estricta de cuadre."""
    print("\n" + "=" * 65)
    print("       REGISTRO DE PARTIDA LIBRE (LÍNEA POR LÍNEA)")
    print("=" * 65)
    glosa = input("Glosa o explicación de la partida: ").strip() or "Asiento de diario personalizado"
    doc = input("Documento de soporte (opcional): ").strip() or None
    fecha = pedir_fecha()

    partida = PartidaDiario(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        glosa=glosa,
        documento_soporte=doc,
    )

    print("\n--- INGRESO DE LÍNEAS (Escriba 'fin' en el código para terminar) ---")
    while True:
        print(f"  Estado actual -> Debe: Q {partida.total_debe:,.2f} | Haber: Q {partida.total_haber:,.2f} | Diferencia: Q {partida.diferencia:,.2f}")
        col = input("  ¿Imputar al Debe [D] o al Haber [H]? (o 'fin' para concluir): ").strip().upper()
        if col == "FIN":
            break
        if col not in ("D", "H"):
            print("  (!) Opción no válida. Ingrese D para Debe o H para Haber.")
            continue

        cod, nom = buscar_o_seleccionar_cuenta("  Código o nombre de cuenta", gestor=gestor)
        monto = pedir_monto(f"  Monto a registrar en el {'DEBE' if col == 'D' else 'HABER'}: Q ")

        if col == "D":
            partida.agregar_cargo(cod, nom, monto)
        else:
            partida.agregar_abono(cod, nom, monto)

    return _guardar_y_mostrar_partida(gestor, partida, "Partida libre registrada exitosamente")