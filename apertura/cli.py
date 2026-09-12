"""Capa de presentación e interacción de consola para el sistema de apertura contable."""
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

from apertura.catalogo import CatalogoService
from apertura.contabilidad import MotorApertura
from apertura.models import CuentaCatalogo, PartidaApertura, ResumenBalance
from config import ARCHIVO_APERTURA_DEFAULT, RESPUESTAS_AFIRMATIVAS
from reportes import exportar_reporte, generar_texto_balance, imprimir_partida_rich
from ui import (
    console,
    formatear_moneda,
    imprimir_alerta,
    imprimir_aviso,
    imprimir_banner,
    imprimir_coincidencias_cuentas,
    imprimir_cuenta_seleccionada,
    imprimir_exito,
    imprimir_menu_clasificacion,
    imprimir_resumen_balance_apertura,
)


def pedir_confirmacion(mensaje: str, default: bool = False) -> bool:
    """Solicita una confirmación sí/no estandarizada al usuario."""
    resp = input(mensaje).strip().lower()
    if not resp:
        return default
    return resp in RESPUESTAS_AFIRMATIVAS


def pedir_monto(cuenta_nombre: str) -> Decimal:
    """Solicita y valida un importe numérico mayor a cero."""
    while True:
        valor = input(f"   -> Monto para '{cuenta_nombre}': Q ").replace(",", "").strip()
        try:
            monto = Decimal(valor)
            if monto <= Decimal("0"):
                imprimir_alerta("El monto debe ser mayor a cero.")
                continue
            return monto.quantize(Decimal("0.01"))
        except InvalidOperation:
            imprimir_alerta("Cantidad inválida. Ingresa un número válido (ej. 15000.50).")


def pedir_clasificacion_manual(nombre: str) -> str:
    """Solicita al usuario clasificar manualmente una cuenta no hallada en catálogo."""
    imprimir_menu_clasificacion(nombre)
    return input("   Opción (1-5): ").strip()


def mostrar_cuentas_registradas(motor: MotorApertura) -> None:
    """Imprime en consola las cuentas registradas hasta el momento con tabla Rich."""
    items = motor.items
    if not items:
        imprimir_alerta("No hay cuentas registradas aún.")
        return

    from ui.tablas import generar_tabla_cuentas_registradas

    tabla = generar_tabla_cuentas_registradas(items)
    console.print(tabla)


def seleccionar_cuenta_interactiva(catalogo: CatalogoService, entrada: str) -> Optional[CuentaCatalogo]:
    """Busca coincidencias y, si hay varias, permite al usuario seleccionar interactivamente."""
    coincidencias = catalogo.buscar_coincidencias(entrada)
    if not coincidencias:
        return None

    if len(coincidencias) == 1:
        c = coincidencias[0]
        imprimir_cuenta_seleccionada(c)
        return c

    limite = min(len(coincidencias), 8)
    imprimir_coincidencias_cuentas(coincidencias, limite=limite)

    while True:
        sel = input("   Elija el número de la cuenta o presione Enter para cancelar: ").strip()
        if not sel:
            return None
        if sel.isdigit() and 1 <= int(sel) <= limite:
            c = coincidencias[int(sel) - 1]
            imprimir_cuenta_seleccionada(c)
            return c
        imprimir_alerta(f"Ingrese un número entre 1 y {limite}.")


def resolver_cuenta(catalogo: CatalogoService, entrada: str) -> Optional[CuentaCatalogo]:
    """Resuelve una cuenta vía catálogo interactivo o mediante clasificación manual."""
    cuenta = seleccionar_cuenta_interactiva(catalogo, entrada)
    if cuenta:
        console.print(f"   Ubicación   : [dim]{cuenta.clase} -> {cuenta.subgrupo}[/dim]")
        return cuenta

    pregunta = f"   [!] No se seleccionó cuenta para '{entrada}'. ¿Deseas clasificarla manualmente? (s/n): "
    if pedir_confirmacion(pregunta):
        opcion = pedir_clasificacion_manual(entrada)
        return catalogo.crear_cuenta_manual(entrada, opcion)

    return None


def procesar_comando_especial(comando: str, motor: MotorApertura) -> bool:
    """Ejecuta comandos auxiliares de control ('ver', 'eliminar'). Retorna True si fue reconocido."""
    cmd = comando.lower()
    if cmd in ("ver", "listar"):
        mostrar_cuentas_registradas(motor)
        return True

    if cmd in ("eliminar", "borrar", "quitar"):
        target = input("   Nombre o código de la cuenta a eliminar: ").strip()
        if motor.eliminar(target):
            imprimir_exito(f"Cuenta '{target}' eliminada.")
        else:
            imprimir_alerta(f"No se encontró la cuenta '{target}'.")
        return True

    return False


def mostrar_guia_comandos() -> None:
    """Muestra el encabezado y comandos especiales del flujo de apertura."""
    imprimir_banner("SISTEMA DE APERTURA CONTABLE: BALANCE Y PARTIDA DE DIARIO", border_style="cyan")
    console.print("Ingresa el código o nombre de cada cuenta. [bold]Comandos especiales:[/bold]")
    console.print("  [cyan]'ver'[/cyan]      : Listar cuentas acumuladas")
    console.print("  [cyan]'eliminar'[/cyan] : Quitar una cuenta")
    console.print("  [cyan]'fin'[/cyan]      : Finalizar y generar Balance y Partida\n")


def ajustar_capital_si_procede(motor: MotorApertura, catalogo: CatalogoService, resumen: ResumenBalance) -> ResumenBalance:
    """Evalúa la diferencia de capital del balance y permite asignarla automáticamente."""
    if resumen.diferencia_capital == Decimal("0.00"):
        return resumen

    imprimir_resumen_balance_apertura(resumen)

    if resumen.diferencia_capital > Decimal("0.00"):
        console.print(f"  Capital residual necesario para cuadrar: [bold yellow]{formatear_moneda(resumen.diferencia_capital)}[/bold yellow]")
        if pedir_confirmacion("¿Deseas asignar esta diferencia a la cuenta de Capital? (s/n): "):
            cta_cap = catalogo.obtener_cuenta_capital()
            motor.asignar_diferencia_capital(cta_cap, resumen.diferencia_capital)
            console.print(
                f"   [green]->[/green] Asignado [bold green]{formatear_moneda(resumen.diferencia_capital)}[/bold green] "
                f"a [[cyan]{cta_cap.codigo}[/cyan]] {cta_cap.nombre}."
            )
            return motor.calcular_balance()
    else:
        imprimir_aviso(
            f"El Pasivo y Patrimonio superan al Activo por {formatear_moneda(abs(resumen.diferencia_capital))}. "
            "Revisa los saldos ingresados; no se asignará capital negativo automático."
        )

    return resumen


def exportar_reportes_si_solicitado(resumen: ResumenBalance, partida: PartidaApertura) -> None:
    """Pregunta al usuario si desea persistir los reportes generados a un archivo de texto."""
    if not pedir_confirmacion("¿Deseas guardar estos reportes en un archivo de texto? (s/n) [n]: ", default=False):
        return

    nombre_arch = input(f"Nombre de archivo [{ARCHIVO_APERTURA_DEFAULT}]: ").strip() or ARCHIVO_APERTURA_DEFAULT
    ruta_completa = exportar_reporte(resumen, partida, nombre_arch)
    imprimir_exito(f"Reporte exportado exitosamente en:\n        {ruta_completa}\n")


def iniciar_flujo_apertura(
    numero_partida: int = 1,
    exportar_archivo: bool = True,
    imprimir_reportes: bool = True,
) -> Tuple[Optional[ResumenBalance], Optional[PartidaApertura]]:
    """Punto de entrada interactivo principal. Retorna (ResumenBalance, PartidaApertura) o (None, None)."""
    mostrar_guia_comandos()

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
        if entrada.lower() == "fin":
            break
        if procesar_comando_especial(entrada, motor):
            continue

        cuenta_info = resolver_cuenta(catalogo, entrada)
        if not cuenta_info:
            continue

        monto = pedir_monto(cuenta_info.nombre)
        registrada = motor.agregar_o_acumular(cuenta_info, monto)
        imprimir_exito(f"Registrado: {formatear_moneda(registrada.monto)} en '{registrada.nombre}' ({registrada.subgrupo}).")

    if not motor.items:
        imprimir_aviso("No se registraron cuentas. Saliendo del programa.")
        return None, None

    resumen = ajustar_capital_si_procede(motor, catalogo, motor.calcular_balance())
    partida = motor.generar_partida_apertura(numero=numero_partida)

    if imprimir_reportes:
        console.print("\n" + generar_texto_balance(resumen))
        imprimir_partida_rich(partida)

    if exportar_archivo:
        exportar_reportes_si_solicitado(resumen, partida)

    return resumen, partida
