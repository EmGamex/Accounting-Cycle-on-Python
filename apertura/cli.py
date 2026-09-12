"""Capa de presentación e interacción de consola para el sistema de apertura contable."""
from decimal import Decimal, InvalidOperation
import sys
from typing import Optional, Tuple

from apertura.catalogo import CatalogoService
from apertura.contabilidad import MotorApertura
from apertura.models import CuentaCatalogo, PartidaApertura, ResumenBalance
from reportes import exportar_reporte, generar_texto_balance, generar_texto_partida, imprimir_partida_rich
from ui import console, imprimir_alerta, imprimir_aviso, imprimir_banner, imprimir_exito


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
    console.print(f"\n   [bold yellow][!][/bold yellow] '{nombre}' no se encontró en el catálogo.")
    print("   Clasifícala:")
    print("   1. Activo Corriente     | 2. Activo No Corriente")
    print("   3. Pasivo Corriente    | 4. Pasivo No Corriente")
    print("   5. Capital / Patrimonio")
    return input("   Opción (1-5): ").strip()


def mostrar_cuentas_registradas(motor: MotorApertura) -> None:
    """Imprime en consola las cuentas registradas hasta el momento con tabla Rich."""
    items = motor.items
    if not items:
        imprimir_alerta("No hay cuentas registradas aún.")
        return

    from rich import box
    from rich.table import Table

    tabla = Table(title="Cuentas Registradas Actualmente", box=box.ROUNDED)
    tabla.add_column("Código", style="dim cyan")
    tabla.add_column("Nombre", style="white")
    tabla.add_column("Tipo", style="yellow")
    tabla.add_column("Monto (Q)", justify="right", style="bold green")

    for cta in items:
        tipo = "(-)" if cta.es_regularizadora else "Normal"
        tabla.add_row(cta.codigo, cta.nombre, tipo, f"Q{cta.monto:,.2f}")

    console.print(tabla)


def seleccionar_cuenta_interactiva(catalogo: CatalogoService, entrada: str) -> Optional[CuentaCatalogo]:
    """Busca coincidencias y, si hay varias, permite al usuario seleccionar interactivamente."""
    coincidencias = catalogo.buscar_coincidencias(entrada)
    if not coincidencias:
        return None

    if len(coincidencias) == 1:
        c = coincidencias[0]
        tag_reg = " (Cuenta Regularizadora)" if c.es_regularizadora else ""
        print(f"   -> Seleccionada: [{c.codigo}] {c.nombre}{tag_reg}")
        return c

    print(f"\n   Coincidencias encontradas ({len(coincidencias)}):")
    limite = min(len(coincidencias), 8)
    for idx, c in enumerate(coincidencias[:limite], 1):
        tag_reg = " (-)" if c.es_regularizadora else "    "
        print(f"     [{idx}] {c.codigo:<9} {tag_reg} {c.nombre}")

    while True:
        sel = input("   Elija el número de la cuenta o presione Enter para cancelar: ").strip()
        if not sel:
            return None
        if sel.isdigit() and 1 <= int(sel) <= limite:
            c = coincidencias[int(sel) - 1]
            tag_reg = " (Cuenta Regularizadora)" if c.es_regularizadora else ""
            print(f"   -> Seleccionada: [{c.codigo}] {c.nombre}{tag_reg}")
            return c
        print(f"   (!) Ingrese un número entre 1 y {limite}.")


def iniciar_flujo_apertura(
    numero_partida: int = 1,
    exportar_archivo: bool = True,
    imprimir_reportes: bool = True,
) -> Tuple[Optional[ResumenBalance], Optional[PartidaApertura]]:
    """Punto de entrada interactivo principal. Retorna (ResumenBalance, PartidaApertura) o (None, None)."""
    imprimir_banner("SISTEMA DE APERTURA CONTABLE: BALANCE Y PARTIDA DE DIARIO", border_style="cyan")
    console.print("Ingresa el código o nombre de cada cuenta. [bold]Comandos especiales:[/bold]")
    console.print("  [cyan]'ver'[/cyan]      : Listar cuentas acumuladas")
    console.print("  [cyan]'eliminar'[/cyan] : Quitar una cuenta")
    console.print("  [cyan]'fin'[/cyan]      : Finalizar y generar Balance y Partida\n")

    try:
        catalogo = CatalogoService.desde_modulo()
    except RuntimeError as e:
        imprimir_alerta(f"{e}")
        return None, None

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
                imprimir_exito(f"Cuenta '{target}' eliminada.")
            else:
                imprimir_alerta(f"No se encontró la cuenta '{target}'.")
            continue

        # Búsqueda interactiva en catálogo
        cuenta_info = seleccionar_cuenta_interactiva(catalogo, entrada)
        if not cuenta_info:
            resp = input(f"   [!] No se seleccionó cuenta para '{entrada}'. ¿Deseas clasificarla manualmente? (s/n): ").strip().lower()
            if resp in ("s", "si", "y", "yes"):
                opcion = pedir_clasificacion_manual(entrada)
                cuenta_info = catalogo.crear_cuenta_manual(entrada, opcion)
            else:
                continue
        else:
            print(f"   Ubicación   : {cuenta_info.clase} -> {cuenta_info.subgrupo}")

        monto = pedir_monto(cuenta_info.nombre)
        registrada = motor.agregar_o_acumular(cuenta_info, monto)
        imprimir_exito(f"Registrado: Q{registrada.monto:,.2f} en '{registrada.nombre}' ({registrada.subgrupo}).")

    if not motor.items:
        print("\nNo se registraron cuentas. Saliendo del programa.")
        return None, None

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
    partida = motor.generar_partida_apertura(numero=numero_partida)

    if imprimir_reportes:
        print("\n" + generar_texto_balance(resumen))
        imprimir_partida_rich(partida)

    # Preguntar si se desea exportar a archivo si está habilitado
    if exportar_archivo:
        exportar = input("¿Deseas guardar estos reportes en un archivo de texto? (s/n) [n]: ").strip().lower()
        if exportar in ("s", "si", "y", "yes"):
            nombre_arch = input("Nombre de archivo [apertura_contable.txt]: ").strip() or "apertura_contable.txt"
            ruta_completa = exportar_reporte(resumen, partida, nombre_arch)
            imprimir_exito(f"Reporte exportado exitosamente en:\n        {ruta_completa}\n")

    return resumen, partida
