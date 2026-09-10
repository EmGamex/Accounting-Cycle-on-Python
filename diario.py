"""Punto de entrada principal interactivo para el Libro Diario."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import sys
from typing import Optional

import catalogo_contable
from diario import (
    CorrelativoError,
    CuentaInvalidaError,
    DescuadrePartidaError,
    GestorLibroDiario,
    MovimientoLinea,
    PartidaDiario,
    TipoOrigenPartida,
    crear_partida_compra,
    crear_partida_simple,
    crear_partida_venta,
    de_partida_apertura,
    de_partida_planilla,
    generar_texto_libro_diario,
    generar_texto_partida,
)
from apertura import CatalogoService, MotorApertura
from planilla import DatosEmpleado, calcular_boleta, generar_partida_contable

gestor = GestorLibroDiario(estricto_cronologico=False)


def pedir_fecha(mensaje: str = "Fecha (DD/MM/AAAA) [Hoy]: ") -> date:
    """Solicita una fecha por consola con valor por defecto la fecha actual."""
    entrada = input(mensaje).strip()
    if not entrada:
        return date.today()
    try:
        return datetime.strptime(entrada, "%d/%m/%Y").date()
    except ValueError:
        print("  (!) Formato inválido. Se usará la fecha de hoy.")
        return date.today()


def pedir_monto(mensaje: str) -> Decimal:
    """Solicita un monto decimal positivo."""
    while True:
        entrada = input(mensaje).strip().replace("Q", "").replace(",", "")
        try:
            val = Decimal(entrada).quantize(Decimal("0.01"))
            if val <= Decimal("0.00"):
                print("  (!) El monto debe ser mayor a 0.00.")
                continue
            return val
        except (InvalidOperation, ValueError):
            print("  (!) Monto no válido. Ingrese un valor numérico (ej. 1500.50).")


def buscar_o_seleccionar_cuenta(mensaje: str, default_codigo: Optional[str] = None) -> tuple[str, str]:
    """Permite ingresar un código contable o buscarlo interactivamente por nombre."""
    prompt = f"{mensaje} [{default_codigo}]: " if default_codigo else f"{mensaje}: "
    while True:
        entrada = input(prompt).strip()
        if not entrada and default_codigo:
            entrada = default_codigo

        if not entrada:
            print("  (!) Debe ingresar un código o nombre de cuenta.")
            continue

        # Si el código existe exactamente
        if gestor.validar_cuenta(entrada):
            nombre = gestor._catalogo_codigos[entrada]
            return entrada, nombre

        # Búsqueda por término
        coincidencias = catalogo_contable.buscar_cuenta(entrada)
        if not coincidencias:
            print(f"  (!) No se encontró ninguna cuenta para '{entrada}'. Intente nuevamente.")
            continue

        if len(coincidencias) == 1:
            _, _, cod, nom = coincidencias[0]
            print(f"      -> Seleccionada: [{cod}] {nom}")
            return cod, nom

        print(f"  Coincidencias encontradas ({len(coincidencias)}):")
        for idx, (_, _, cod, nom) in enumerate(coincidencias[:7], 1):
            print(f"    [{idx}] {cod:<9} {nom}")
        sel = input("  Elija el número de la cuenta o presione Enter para buscar otra vez: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(coincidencias[:7]):
            _, _, cod, nom = coincidencias[int(sel) - 1]
            return cod, nom


def registrar_apertura_asistida():
    """Genera y registra la Partida #1 a partir de un balance inicial de apertura."""
    print("\n" + "=" * 65)
    print("      REGISTRO DE PARTIDA No. 1 - BALANCE DE APERTURA")
    print("=" * 65)
    print("  [1] Generar apertura con datos de ejemplo (Caja, Bancos, Mercaderías, Capital)")
    print("  [2] Ingresar saldos iniciales cuenta por cuenta")
    opcion = input("\nSeleccione [1]: ").strip() or "1"

    cat = CatalogoService.desde_modulo()
    motor_ap = MotorApertura()

    if opcion == "1":
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
    else:
        print("  Ingrese las cuentas de apertura (escriba 'fin' para terminar):")
        while True:
            cta_txt = input("\nCuenta o código ('fin' para calcular capital): ").strip()
            if cta_txt.lower() == "fin":
                break
            cta = cat.buscar(cta_txt)
            if not cta:
                print("  (!) Cuenta no reconocida en catálogo.")
                continue
            monto = pedir_monto(f"  Saldo para {cta.nombre}: ")
            motor_ap.agregar_o_acumular(cta, monto)

        res = motor_ap.calcular_balance()
        print(f"\n  Total Activo: Q {res.total_activo:,.2f} | Pasivo: Q {res.total_pasivo:,.2f}")
        print(f"  Diferencia calculada de Capital: Q {res.diferencia_capital:,.2f}")
        cta_capital = cat.buscar("3101")
        if cta_capital:
            motor_ap.asignar_diferencia_capital(cta_capital, res.diferencia_capital)

    fecha = pedir_fecha("Fecha del asiento de apertura [Hoy]: ")
    pda_ap = motor_ap.generar_partida_apertura(numero=gestor.siguiente_numero)
    partida_diario = de_partida_apertura(pda_ap, fecha=fecha, numero=gestor.siguiente_numero)

    try:
        gestor.registrar_partida(partida_diario)
        print("\n  [OK] Partida registrada exitosamente:")
        print(generar_texto_partida(partida_diario))
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")


def registrar_nomina_asistida():
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
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")


def registrar_compra_asistida():
    """Registra una compra con desglose automático de Crédito Fiscal IVA (12%)."""
    print("\n" + "=" * 65)
    print("          REGISTRO DE COMPRA O GASTO CON IVA (12%)")
    print("=" * 65)
    glosa = input("Descripción o concepto de la compra: ").strip() or "Compra de bienes/servicios para la empresa"
    doc = input("No. de Factura / Documento: ").strip() or "FAC-001"
    total = pedir_monto("Total de la factura (IVA incluido): Q ")

    cod_gasto, nom_gasto = buscar_o_seleccionar_cuenta("Cuenta de gasto o activo", default_codigo="5201")
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
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")


def registrar_venta_asistida():
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
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")


def registrar_operacion_simple_asistida():
    """Registra una operación simple de 2 cuentas (cargo y abono)."""
    print("\n" + "=" * 65)
    print("          REGISTRO DE OPERACIÓN SIMPLE (2 CUENTAS)")
    print("=" * 65)
    glosa = input("Descripción de la operación: ").strip() or "Traslado o pago simple"
    monto = pedir_monto("Monto total de la operación: Q ")
    cod_debe, nom_debe = buscar_o_seleccionar_cuenta("Cuenta que recibe el cargo (DEBE)", default_codigo="1102")
    cod_haber, nom_haber = buscar_o_seleccionar_cuenta("Cuenta que entrega el abono (HABER)", default_codigo="1101")
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
    )

    try:
        gestor.registrar_partida(partida)
        print("\n  [OK] Partida simple registrada:")
        print(generar_texto_partida(partida))
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")


def registrar_partida_libre_asistida():
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

        cod, nom = buscar_o_seleccionar_cuenta("  Código o nombre de cuenta")
        monto = pedir_monto(f"  Monto a registrar en el {'DEBE' if col == 'D' else 'HABER'}: Q ")

        if col == "D":
            partida.agregar_cargo(cod, nom, monto)
        else:
            partida.agregar_abono(cod, nom, monto)

    try:
        gestor.registrar_partida(partida)
        print("\n  [OK] Partida libre registrada exitosamente:")
        print(generar_texto_partida(partida))
    except DescuadrePartidaError as e:
        print(f"\n  [ERROR DE CUADRE] {e}")
        print("  La partida no se registró porque violaría el principio de partida doble.")
    except Exception as e:
        print(f"\n  (!) Error al registrar partida: {e}")


def main():
    print("=" * 70)
    print("         SISTEMA DE LIBRO DIARIO CONTABLE (GUATEMALA)")
    print("=" * 70)

    while True:
        num_partidas = len(gestor.libro.partidas)
        print(f"\nLibro Diario Actual: {num_partidas} partida(s) registradas | Siguiente: Partida #{gestor.siguiente_numero}")
        print("Opciones disponibles:")
        print("  [1] Registrar Partida #1 de Apertura (Asistida / Demo)")
        print("  [2] Registrar Partida de Nómina de Sueldos (Asistida / Demo)")
        print("  [3] Registrar Compra / Gasto con IVA (Crédito Fiscal 12%)")
        print("  [4] Registrar Venta con IVA (Débito Fiscal 12%)")
        print("  [5] Registrar Operación Simple (Traslado, Cobro, Pago)")
        print("  [6] Registrar Partida Libre (Línea por línea)")
        print("  [7] Ver Libro Diario Completo")
        print("  [0] Salir")

        opcion = input("\nSeleccione una opción [1-7, 0]: ").strip()

        if opcion == "1":
            registrar_apertura_asistida()
        elif opcion == "2":
            registrar_nomina_asistida()
        elif opcion == "3":
            registrar_compra_asistida()
        elif opcion == "4":
            registrar_venta_asistida()
        elif opcion == "5":
            registrar_operacion_simple_asistida()
        elif opcion == "6":
            registrar_partida_libre_asistida()
        elif opcion == "7":
            print("\n" + generar_texto_libro_diario(gestor.libro))
        elif opcion == "0":
            print("\n¡Gracias por utilizar el Sistema de Libro Diario!")
            break
        else:
            print("  (!) Opción no reconocida. Intente nuevamente.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario. Saliendo...")
        sys.exit(0)
