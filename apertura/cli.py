"""Capa de presentación e interacción de consola para el sistema de apertura contable."""
from decimal import Decimal, InvalidOperation
from typing import Callable, List, NamedTuple, Optional, Tuple

from apertura.catalogo import CatalogoService, normalizar
from apertura.contabilidad import MotorApertura
from apertura.models import CuentaCatalogo, ItemCuentaApertura, PartidaApertura, ResumenBalance
from config import (
    ARCHIVO_APERTURA_DEFAULT,
    CERO_MONETARIO,
    MENSAJE_ALERTA_OPCION,
    OPCION_SALIR,
    PRECISION_CENTAVOS,
)
from reportes import exportar_reporte
from ui import (
    console,
    formatear_moneda,
    generar_tabla_cuentas_registradas,
    imprimir_alerta,
    imprimir_aviso,
    imprimir_balance_apertura_rich,
    imprimir_banner,
    imprimir_exito,
    imprimir_menu_clasificacion,
    imprimir_menu_opciones,
    imprimir_partida_rich,
    imprimir_resumen_balance_apertura,
    pedir_confirmacion,
    seleccionar_coincidencia_interactiva,
)

# Constantes de control y límites visuales específicas de apertura
MAX_COINCIDENCIAS_MOSTRADAS: int = 8
OPCIONES_CLASIFICACION_RANGO: str = "1-5"
OPCIONES_CLASIFICACION_VALIDAS: tuple = ("1", "2", "3", "4", "5")


class AccionMenu(NamedTuple):
    """Estructura para representar una opción ejecutable en el menú de apertura."""
    descripcion: str
    accion: Callable[[], None]


def pedir_monto(cuenta_nombre: str) -> Decimal:
    """Solicita y valida un importe numérico mayor a cero."""
    while True:
        valor = input(f"   -> Monto para '{cuenta_nombre}': Q ").replace(",", "").strip()
        try:
            monto = Decimal(valor)
            if monto <= CERO_MONETARIO:
                imprimir_alerta("El monto debe ser mayor a cero.")
                continue
            return monto.quantize(PRECISION_CENTAVOS)
        except InvalidOperation:
            imprimir_alerta("Cantidad inválida. Ingresa un número válido (ej. 15000.50).")


def pedir_clasificacion_manual(nombre: str) -> str:
    """Solicita al usuario clasificar manualmente una cuenta no hallada en catálogo."""
    imprimir_menu_clasificacion(nombre)
    while True:
        opcion = input(f"   Opción ({OPCIONES_CLASIFICACION_RANGO}): ").strip()
        if opcion in OPCIONES_CLASIFICACION_VALIDAS:
            return opcion
        imprimir_alerta(MENSAJE_ALERTA_OPCION)


def mostrar_cuentas_registradas(motor: MotorApertura) -> None:
    """Imprime en consola las cuentas registradas hasta el momento con tabla Rich."""
    items = motor.items
    if not items:
        imprimir_alerta("No hay cuentas registradas aún.")
        return

    tabla = generar_tabla_cuentas_registradas(items)
    console.print(tabla)


def seleccionar_cuenta_interactiva(catalogo: CatalogoService, entrada: str) -> Optional[CuentaCatalogo]:
    """Busca coincidencias y, si hay varias, permite al usuario seleccionar interactivamente."""
    coincidencias = catalogo.buscar_coincidencias(entrada)
    return seleccionar_coincidencia_interactiva(
        coincidencias,
        limite=MAX_COINCIDENCIAS_MOSTRADAS,
        mostrar_feedback=True,
        mensaje_prompt="   Elija el número de la cuenta o presione Enter para cancelar: ",
        permitir_reintento=True,
    )


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


def _registrar_cuentas(motor: MotorApertura, catalogo: CatalogoService) -> None:
    """Bucle continuo para ingresar cuentas y montos hasta presionar Enter vacío."""
    console.print("\n[bold]Ingreso de Cuentas y Saldos Iniciales:[/bold]")
    console.print("  [dim]Presiona Enter en blanco en el prompt de cuenta para regresar al menú.[/dim]")
    while True:
        entrada = input("\n   Cuenta o código (Enter para volver): ").strip()
        if not entrada:
            break

        cuenta_info = resolver_cuenta(catalogo, entrada)
        if not cuenta_info:
            continue

        monto = pedir_monto(cuenta_info.nombre)
        registrada = motor.agregar_o_acumular(cuenta_info, monto)
        imprimir_exito(f"Registrado: {formatear_moneda(registrada.monto)} en '{registrada.nombre}' ({registrada.subgrupo}).")


def _ver_balance_situacion(motor: MotorApertura) -> None:
    """Calcula y muestra el Balance de Situación General de Apertura en Rich."""
    if not motor.items:
        imprimir_alerta("No hay cuentas registradas aún para generar el balance.")
        return
    resumen = motor.calcular_balance()
    console.print("")
    imprimir_balance_apertura_rich(resumen)


def _modificar_monto_cuenta(motor: MotorApertura) -> None:
    """Solicita una cuenta y actualiza su saldo inicial."""
    if not motor.items:
        imprimir_alerta("No hay cuentas registradas para modificar.")
        return

    target = input("   Nombre o código de la cuenta a modificar: ").strip()
    if not target:
        return

    cta_existente = None
    for it in motor.items:
        if it.codigo == target or normalizar(it.nombre) == normalizar(target):
            cta_existente = it
            break

    if not cta_existente:
        imprimir_alerta(f"No se encontró la cuenta '{target}'.")
        return

    nuevo_monto = pedir_monto(cta_existente.nombre)
    modificado = motor.modificar_monto(target, nuevo_monto)
    if modificado:
        imprimir_exito(f"Monto de '{modificado.nombre}' actualizado a {formatear_moneda(modificado.monto)}.")


def _eliminar_cuenta(motor: MotorApertura) -> None:
    """Elimina una cuenta del inventario de apertura."""
    if not motor.items:
        imprimir_alerta("No hay cuentas registradas para eliminar.")
        return

    target = input("   Nombre o código de la cuenta a eliminar: ").strip()
    if not target:
        return

    if motor.eliminar(target):
        imprimir_exito(f"Cuenta '{target}' eliminada del balance de apertura.")
    else:
        imprimir_alerta(f"No se encontró la cuenta '{target}'.")


def ajustar_capital_si_procede(motor: MotorApertura, catalogo: CatalogoService, resumen: ResumenBalance) -> ResumenBalance:
    """Evalúa la diferencia de capital del balance y permite asignarla automáticamente."""
    if resumen.diferencia_capital == CERO_MONETARIO:
        return resumen

    imprimir_resumen_balance_apertura(resumen)

    if resumen.diferencia_capital > CERO_MONETARIO:
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
    cuentas_iniciales: Optional[List[ItemCuentaApertura]] = None,
) -> Tuple[Optional[ResumenBalance], Optional[PartidaApertura]]:
    """Punto de entrada interactivo principal. Retorna (ResumenBalance, PartidaApertura) o (None, None)."""
    try:
        catalogo = CatalogoService.desde_modulo()
    except RuntimeError as e:
        imprimir_alerta(f"{e}")
        return None, None

    motor = MotorApertura(items_iniciales=cuentas_iniciales)

    imprimir_banner("SISTEMA DE APERTURA CONTABLE: BALANCE Y PARTIDA DE DIARIO", border_style="cyan")

    if motor.items:
        imprimir_aviso(
            f"Se precargaron {len(motor.items)} cuentas de apertura previas del ejercicio.\n"
            f"   Puedes revisarlas con la opción 2 o ver el balance en la opción 3."
        )

    acciones = [
        AccionMenu("Registrar cuentas de apertura", lambda: _registrar_cuentas(motor, catalogo)),
        AccionMenu("Ver cuentas registradas", lambda: mostrar_cuentas_registradas(motor)),
        AccionMenu("Ver Balance de Situación General de Apertura (Rich)", lambda: _ver_balance_situacion(motor)),
        AccionMenu("Modificar saldo de una cuenta", lambda: _modificar_monto_cuenta(motor)),
        AccionMenu("Eliminar cuenta registrada", lambda: _eliminar_cuenta(motor)),
        AccionMenu("Finalizar apertura y generar Partida #1", lambda: None),
    ]

    while True:
        console.print("\n[bold]Operaciones de Apertura Contable disponibles:[/bold]")
        opciones = [(str(idx), item.descripcion) for idx, item in enumerate(acciones, start=1)]
        imprimir_menu_opciones(opciones, texto_salir="Volver al menú principal", salir_codigo=OPCION_SALIR)

        seleccion = input(f"\nSeleccione una opción [1-{len(acciones)}, {OPCION_SALIR}]: ").strip()
        if seleccion == OPCION_SALIR:
            if motor.items and not pedir_confirmacion("Hay cuentas registradas. ¿Deseas salir sin generar la apertura? (s/n): ", default=False):
                continue
            return None, None

        if seleccion == "6":
            if not motor.items:
                imprimir_alerta("Debes registrar al menos una cuenta para finalizar la apertura.")
                continue
            break

        if seleccion.isdigit() and 1 <= int(seleccion) <= len(acciones):
            acciones[int(seleccion) - 1].accion()
        else:
            imprimir_alerta(MENSAJE_ALERTA_OPCION)

    resumen = ajustar_capital_si_procede(motor, catalogo, motor.calcular_balance())
    partida = motor.generar_partida_apertura(numero=numero_partida)

    if imprimir_reportes:
        console.print("")
        imprimir_balance_apertura_rich(resumen)
        console.print("")
        imprimir_partida_rich(partida)

    if exportar_archivo:
        exportar_reportes_si_solicitado(resumen, partida)

    return resumen, partida

