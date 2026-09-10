"""Asistentes interactivos de captura guiada de operaciones para el Libro Diario."""
from decimal import Decimal
from typing import Optional

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
        for cod, monto in [
            ("1101", Decimal("10000.00")),  # Caja General
            ("1102", Decimal("45000.00")),  # Bancos
            ("1104", Decimal("30000.00")),  # Mercaderías
            ("1204", Decimal("15000.00")),  # Mobiliario
            ("2101", Decimal("20000.00")),  # Proveedores
        ]:
            cta = cat.buscar(cod)
            if cta:
                motor_ap.agregar_o_acumular(cta, monto)
        res = motor_ap.calcular_balance()
        cta_capital = cat.buscar("3101")
        if cta_capital:
            motor_ap.asignar_diferencia_capital(cta_capital, res.diferencia_capital)

        fecha = pedir_fecha("Fecha del asiento de apertura [Hoy]: ")
        pda_ap = motor_ap.generar_partida_apertura(numero=gestor.siguiente_numero)
    else:
        # Usa el flujo completo e interactivo de apertura-cuentas (con ver, eliminar, clasificar, etc.)
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

    try:
        gestor.registrar_partida(partida_diario)
        print("\n  [OK] Partida registrada exitosamente:")
        print(generar_texto_partida(partida_diario))
        return partida_diario
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")
        return None


def registrar_nomina_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Genera y registra la partida de sueldos desde el módulo de planilla."""
    print("\n" + "=" * 65)
    print("           REGISTRO DE PARTIDA DE SUELDOS Y SALARIOS")
    print("=" * 65)
    print("  [1] Generar nómina de ejemplo (Administración y Ventas)")
    print("  [2] Ingresar empleado manualmente")
    opcion = input("\nSeleccione [1]: ").strip() or "1"

    if opcion == "1":
        empleados = [
            DatosEmpleado("Juan Morales", Decimal("5500.00"), departamento="Administración", horas_extras=Decimal("4.0")),
            DatosEmpleado("Ana Castillo", Decimal("4000.00"), departamento="Ventas", ventas=Decimal("35000.00"), pct_comision=Decimal("0.03")),
        ]
        resultados = [calcular_boleta(e) for e in empleados]
    else:
        nombre = input("Nombre del empleado: ").strip() or "Empleado 1"
        depto = input("Departamento (Administración/Ventas) [Administración]: ").strip() or "Administración"
        sueldo = pedir_monto("Sueldo Base: ")
        emp = DatosEmpleado(nombre=nombre, sueldo_base=sueldo, departamento=depto)
        resultados = [calcular_boleta(emp)]

    pda_contable = generar_partida_contable(resultados)
    fecha = pedir_fecha("Fecha de liquidación [Hoy]: ")
    partida_diario = de_partida_planilla(pda_contable, fecha=fecha, numero=gestor.siguiente_numero)

    try:
        gestor.registrar_partida(partida_diario)
        print("\n  [OK] Partida de nómina registrada exitosamente:")
        print(generar_texto_partida(partida_diario))
        return partida_diario
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")
        return None


def registrar_compra_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Registra una compra con desglose automático de Crédito Fiscal IVA (12%)."""
    print("\n" + "=" * 65)
    print("          REGISTRO DE COMPRA O GASTO CON IVA (12%)")
    print("=" * 65)
    glosa = input("Descripción o concepto de la compra: ").strip() or "Compra de bienes/servicios para la empresa"
    doc = input("No. de Factura / Documento: ").strip() or "FAC-001"
    total = pedir_monto("Total de la factura (IVA incluido): Q ")

    cod_gasto, nom_gasto = buscar_o_seleccionar_cuenta("Cuenta de gasto o activo", default_codigo="5201", gestor=gestor)
    fecha = pedir_fecha()

    print("\n  Condición de pago:")
    print("    [1] 100% Contado (Bancos o Caja)")
    print("    [2] 100% Crédito (Proveedores Locales)")
    print("    [3] Mixto (ej. Transferencia Bancos + Saldo a Proveedores)")
    cond = input("  Seleccione [1-3] (Default [1]): ").strip() or "1"

    pct_efectivo = Decimal("0.00")
    pct_banco = Decimal("0.00")
    pct_prov = Decimal("0.00")

    if cond == "2":
        pct_prov = Decimal("1.00")
    elif cond == "3":
        pct_in = input("    % a pagar por Banco/Transferencia (ej. 20): ").strip() or "20"
        pct_banco = Decimal(pct_in) / Decimal("100.00")
        pct_prov = Decimal("1.00") - pct_banco
        print(f"    -> Se asignará {pct_banco * 100:.1f}% a Bancos y {pct_prov * 100:.1f}% a Proveedores.")
    else:
        medio = input("    ¿Pagar con Bancos [B] o Caja/Efectivo [C]? (Default [B]): ").strip().upper() or "B"
        if medio == "C":
            pct_efectivo = Decimal("1.00")
        else:
            pct_banco = Decimal("1.00")

    partida = crear_partida_compra(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        glosa=glosa,
        total_factura=total,
        codigo_gasto=cod_gasto,
        nombre_gasto=nom_gasto,
        pct_efectivo=pct_efectivo,
        pct_banco=pct_banco,
        pct_proveedores=pct_prov,
        documento_soporte=doc,
    )

    try:
        gestor.registrar_partida(partida)
        print("\n  [OK] Partida de compra registrada:")
        print(generar_texto_partida(partida))
        return partida
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")
        return None


def registrar_venta_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Registra una venta con desglose automático de Débito Fiscal IVA (12%)."""
    print("\n" + "=" * 65)
    print("          REGISTRO DE VENTA CON IVA (12%)")
    print("=" * 65)
    glosa = input("Descripción o concepto de la venta: ").strip() or "Venta de mercaderías"
    doc = input("No. de Factura emitida (FEL): ").strip() or "FEL"
    total = pedir_monto("Total de la venta (IVA incluido): Q ")
    fecha = pedir_fecha()

    print("\n  Condición de cobro:")
    print("    [1] 100% Contado (Bancos o Caja)")
    print("    [2] 100% Crédito (Cuentas por Cobrar Clientes)")
    print("    [3] Mixto (ej. Transferencia Bancaria + Saldo a Crédito)")
    cond = input("  Seleccione [1-3] (Default [1]): ").strip() or "1"

    pct_efectivo = Decimal("0.00")
    pct_banco = Decimal("0.00")
    pct_credito = Decimal("0.00")

    if cond == "2":
        pct_credito = Decimal("1.00")
    elif cond == "3":
        pct_in = input("    % a cobrar por Transferencia Bancaria (ej. 60): ").strip() or "60"
        pct_banco = Decimal(pct_in) / Decimal("100.00")
        pct_credito = Decimal("1.00") - pct_banco
        print(f"    -> Se asignará {pct_banco * 100:.1f}% a Bancos y {pct_credito * 100:.1f}% a Clientes.")
    else:
        medio = input("    ¿Cobrar en Bancos [B] o Caja/Efectivo [C]? (Default [B]): ").strip().upper() or "B"
        if medio == "C":
            pct_efectivo = Decimal("1.00")
        else:
            pct_banco = Decimal("1.00")

    partida = crear_partida_venta(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        glosa=glosa,
        total_factura=total,
        pct_efectivo=pct_efectivo,
        pct_banco=pct_banco,
        pct_credito=pct_credito,
        documento_soporte=doc,
    )

    try:
        gestor.registrar_partida(partida)
        print("\n  [OK] Partida de venta registrada:")
        print(generar_texto_partida(partida))
        return partida
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")
        return None


def registrar_operacion_simple_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Asistente inteligente de operaciones frecuentes (cobros, pagos, depósitos y préstamos)."""
    print("\n" + "=" * 65)
    print("      REGISTRO DE OPERACIONES FRECUENTES (PAGOS Y COBROS)")
    print("=" * 65)
    print("  Seleccione el tipo de operación:")
    print("    [1] Abono / Cobro de Clientes (Clientes nos pagan)")
    print("    [2] Abono / Pago a Proveedores (Pagamos deuda con cheque o efectivo)")
    print("    [3] Depósito en el Banco (Traslado de Caja a Bancos)")
    print("    [4] Retiro del Banco a Caja (Efectivo disponible)")
    print("    [5] Abono / Pago a Préstamo Bancario (Amortización de deuda)")
    print("    [6] Otra operación libre (Elegir cuentas Debe y Haber a medida)")

    tipo = input("\n  Seleccione una opción [1-6] (Default [1]): ").strip() or "1"

    if tipo == "1":
        # Cobro a clientes
        monto = pedir_monto("  Monto abonado por el cliente: Q ")
        medio = input("  ¿Cobrado en Efectivo [E] o Banco/Transferencia/Cheque [B]? (Default [E]): ").strip().upper() or "E"
        doc = input("  No. de Recibo / Documento de soporte (opcional): ").strip() or None
        fecha = pedir_fecha()
        canal = "banco" if medio == "B" else "caja"
        partida = crear_partida_abono_cliente(
            numero=gestor.siguiente_numero,
            fecha=fecha,
            monto=monto,
            medio=canal,
            documento_soporte=doc,
        )

    elif tipo == "2":
        # Pago a proveedores
        monto = pedir_monto("  Monto a pagar al proveedor: Q ")
        medio = input("  ¿Pagado con Cheque/Transferencia [B] o Efectivo [E]? (Default [B]): ").strip().upper() or "B"
        doc = input("  No. de Cheque / Transferencia (ej. Ch. 4501): ").strip() or None
        fecha = pedir_fecha()
        canal = "caja" if medio == "E" else "banco"
        partida = crear_partida_abono_proveedor(
            numero=gestor.siguiente_numero,
            fecha=fecha,
            monto=monto,
            medio=canal,
            documento_soporte=doc,
        )

    elif tipo == "3":
        # Depósito en el banco
        monto = pedir_monto("  Monto a depositar en el Banco: Q ")
        doc = input("  No. de Boleta de Depósito (opcional): ").strip() or None
        fecha = pedir_fecha()
        partida = crear_partida_deposito_banco(
            numero=gestor.siguiente_numero,
            fecha=fecha,
            monto=monto,
            documento_soporte=doc,
        )

    elif tipo == "4":
        # Retiro de banco a caja
        monto = pedir_monto("  Monto retirado del Banco para Caja: Q ")
        doc = input("  No. de Cheque / Comprobante (opcional): ").strip() or None
        fecha = pedir_fecha()
        partida = crear_partida_retiro_banco(
            numero=gestor.siguiente_numero,
            fecha=fecha,
            monto=monto,
            documento_soporte=doc,
        )

    elif tipo == "5":
        # Abono a préstamo bancario
        monto = pedir_monto("  Monto del abono / amortización al préstamo: Q ")
        doc = input("  No. de Transferencia / Comprobante (opcional): ").strip() or None
        fecha = pedir_fecha()
        partida = crear_partida_abono_prestamo(
            numero=gestor.siguiente_numero,
            fecha=fecha,
            monto=monto,
            documento_soporte=doc,
        )

    else:
        # Operación libre
        glosa = input("  Descripción de la operación: ").strip() or "Operación simple"
        monto = pedir_monto("  Monto total de la operación: Q ")
        cod_debe, nom_debe = buscar_o_seleccionar_cuenta("  Cuenta que recibe el cargo (DEBE)", default_codigo="1102", gestor=gestor)
        cod_haber, nom_haber = buscar_o_seleccionar_cuenta("  Cuenta que entrega el abono (HABER)", default_codigo="1101", gestor=gestor)
        doc = input("  Documento de soporte (opcional): ").strip() or None
        fecha = pedir_fecha()

        partida = crear_partida_simple(
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

    try:
        gestor.registrar_partida(partida)
        print("\n  [OK] Partida registrada exitosamente:")
        print(generar_texto_partida(partida))
        return partida
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")
        return None


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

    try:
        gestor.registrar_partida(partida)
        print("\n  [OK] Partida libre registrada exitosamente:")
        print(generar_texto_partida(partida))
        return partida
    except DescuadrePartidaError as e:
        print(f"\n  [ERROR DE CUADRE] {e}")
        print("  La partida no se registró porque violaría el principio de partida doble.")
        return None
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")
        return None
