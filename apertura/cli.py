"""Capa de presentación e interacción de consola para el sistema de apertura contable."""
from decimal import Decimal, InvalidOperation
import sys
from typing import Optional

from apertura.catalogo import CatalogoService
from apertura.contabilidad import MotorApertura
from apertura.reportes import exportar_reporte, generar_texto_balance, generar_texto_partida


def pedir_monto(cuenta_nombre: str) -> Decimal:
    """Solicita y valida un importe numérico mayor a cero."""
    while True:
        valor = input(f"   -> Monto para '{cuenta_nombre}': Q ").replace(",", "").strip()
        try:
            monto = Decimal(valor)
            if monto <= Decimal("0"):
                print("      El monto debe ser mayor a cero.")
                continue
            return monto.quantize(Decimal("0.01"))
        except InvalidOperation:
            print("      Cantidad inválida. Ingresa un número válido (ej. 15000.50).")


def pedir_clasificacion_manual(nombre: str) -> str:
    """Solicita al usuario clasificar manualmente una cuenta no hallada en catálogo."""
    print(f"\n   [!] '{nombre}' no se encontró en el catálogo.")
    print("   Clasifícala:")
    print("   1. Activo Corriente     | 2. Activo No Corriente")
    print("   3. Pasivo Corriente    | 4. Pasivo No Corriente")
    print("   5. Capital / Patrimonio")
    return input("   Opción (1-5): ").strip()


def mostrar_cuentas_registradas(motor: MotorApertura) -> None:
    """Imprime en consola las cuentas registradas hasta el momento."""
    items = motor.items
    if not items:
        print("\n   [!] No hay cuentas registradas aún.")
        return

    print("\n   " + "-" * 65)
    print("   CUENTAS REGISTRADAS ACTUALMENTE:")
    print(f"   {'CÓDIGO':<8} {'NOMBRE':<35} {'TIPO':<10} {'MONTO (Q)':>12}")
    print("   " + "-" * 65)
    for cta in items:
        tipo = "(-)" if cta.es_regularizadora else "Normal"
        print(f"   {cta.codigo:<8} {cta.nombre:<35} {tipo:<10} {cta.monto:>12,.2f}")
    print("   " + "-" * 65)


def iniciar_flujo_apertura() -> None:
    """Punto de entrada interactivo principal."""
    print("=" * 75)
    print("      SISTEMA DE APERTURA CONTABLE: BALANCE Y PARTIDA DE DIARIO")
    print("=" * 75)
    print("Ingresa el código o nombre de cada cuenta. Comandos especiales:")
    print("  'ver'      : Listar cuentas acumuladas")
    print("  'eliminar' : Quitar una cuenta")
    print("  'fin'      : Finalizar y generar Balance y Partida\n")

    try:
        catalogo = CatalogoService.desde_modulo()
    except RuntimeError as e:
        print(f"\n[ERROR] {e}")
        return

    motor = MotorApertura()

    while True:
        entrada = input("\nCuenta, código o comando (o 'fin'): ").strip()
        if not entrada:
            continue

        cmd = entrada.lower()
        if cmd == "fin":
            break
        elif cmd in ("ver", "listar"):
            mostrar_cuentas_registradas(motor)
            continue
        elif cmd in ("eliminar", "borrar", "quitar"):
            target = input("   Nombre o código de la cuenta a eliminar: ").strip()
            if motor.eliminar(target):
                print(f"   [OK] Cuenta '{target}' eliminada.")
            else:
                print(f"   [!] No se encontró la cuenta '{target}'.")
            continue

        # Búsqueda en catálogo
        cuenta_info = catalogo.buscar(entrada)
        if not cuenta_info:
            opcion = pedir_clasificacion_manual(entrada)
            cuenta_info = catalogo.crear_cuenta_manual(entrada, opcion)
        else:
            tag_reg = " (Cuenta Regularizadora)" if cuenta_info.es_regularizadora else ""
            print(f"   Identificada: [{cuenta_info.codigo}] {cuenta_info.nombre}{tag_reg}")
            print(f"   Ubicación   : {cuenta_info.clase} -> {cuenta_info.subgrupo}")

        monto = pedir_monto(cuenta_info.nombre)
        registrada = motor.agregar_o_acumular(cuenta_info, monto)
        print(f"   Registrado: Q {registrada.monto:,.2f} en '{registrada.nombre}' ({registrada.subgrupo}).")

    if not motor.items:
        print("\nNo se registraron cuentas. Saliendo del programa.")
        return

    # Cálculo del balance
    resumen = motor.calcular_balance()

    # Ajuste residual de capital si es necesario
    if resumen.diferencia_capital != Decimal("0.00"):
        print("\n" + "-" * 75)
        print(
            f"Activo Neto: Q {resumen.total_activo:,.2f} | "
            f"Pasivo: Q {resumen.total_pasivo:,.2f} | "
            f"Patrimonio: Q {resumen.total_patrimonio:,.2f}"
        )

        if resumen.diferencia_capital > Decimal("0.00"):
            print(f"Capital residual necesario para cuadrar: Q {resumen.diferencia_capital:,.2f}")
            ajustar = input("¿Deseas asignar esta diferencia a la cuenta de Capital? (s/n): ").strip().lower()

            if ajustar in ("s", "si", "y", "yes"):
                cta_cap = catalogo.obtener_cuenta_capital()
                motor.asignar_diferencia_capital(cta_cap, resumen.diferencia_capital)
                print(f"   -> Asignado Q {resumen.diferencia_capital:,.2f} a [{cta_cap.codigo}] {cta_cap.nombre}.")
                resumen = motor.calcular_balance()
        else:
            print(
                f"[Aviso] El Pasivo y Patrimonio superan al Activo por Q {abs(resumen.diferencia_capital):,.2f}. "
                "Revisa los saldos ingresados; no se asignará capital negativo automático."
            )

    # Generar reportes
    partida = motor.generar_partida_apertura()

    print("\n" + generar_texto_balance(resumen))
    print(generar_texto_partida(partida))

    # Preguntar si se desea exportar a archivo
    exportar = input("¿Deseas guardar estos reportes en un archivo de texto? (s/n) [n]: ").strip().lower()
    if exportar in ("s", "si", "y", "yes"):
        nombre_arch = input("Nombre de archivo [apertura_contable.txt]: ").strip() or "apertura_contable.txt"
        ruta_completa = exportar_reporte(resumen, partida, nombre_arch)
        print(f"   [OK] Reporte exportado exitosamente en:\n        {ruta_completa}\n")
