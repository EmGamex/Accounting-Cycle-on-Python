"""Asistentes para integración con módulos externos: Apertura y Planillas/Nómina."""
from decimal import Decimal
from typing import Optional, Tuple

from apertura import CatalogoService, MotorApertura, iniciar_flujo_apertura
from planilla import DatosEmpleado, calcular_boleta, generar_partida_contable
from diario.conectores import de_partida_apertura, de_partida_planilla
from diario.engine import GestorLibroDiario
from diario.models import PartidaDiario
from diario.prompts import pedir_fecha, pedir_monto

from ui import console, imprimir_alerta, imprimir_banner
from .comun import (
    COD_BANCOS,
    COD_CAJA,
    COD_CAPITAL,
    COD_MERCADERIAS,
    COD_MOBILIARIO,
    COD_PROVEEDORES,
    guardar_y_mostrar_partida,
)

# Datos semilla demo para apertura
DEMO_APERTURA_ITEMS: Tuple[Tuple[str, Decimal], ...] = (
    (COD_CAJA, Decimal("10000.00")),
    (COD_BANCOS, Decimal("45000.00")),
    (COD_MERCADERIAS, Decimal("30000.00")),
    (COD_MOBILIARIO, Decimal("15000.00")),
    (COD_PROVEEDORES, Decimal("20000.00")),
)

# Datos semilla demo para nómina
DEMO_NOMINA_EMPLEADOS = (
    DatosEmpleado("Juan Morales", Decimal("5500.00"), departamento="Administración", horas_extras=Decimal("4.0")),
    DatosEmpleado("Ana Castillo", Decimal("4000.00"), departamento="Ventas", ventas=Decimal("35000.00"), pct_comision=Decimal("0.03")),
)


def registrar_apertura_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Genera y registra la Partida #1 a partir de un balance inicial de apertura."""
    imprimir_banner("REGISTRO DE PARTIDA No. 1 - BALANCE DE APERTURA", border_style="cyan")
    console.print("  [bold cyan][1][/bold cyan] Generar apertura con datos de ejemplo (Caja, Bancos, Mercaderías, Capital)")
    console.print("  [bold cyan][2][/bold cyan] Ingresar saldos iniciales cuenta por cuenta")
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
        # Usa el flujo interactivo de apertura-cuentas
        _, pda_ap = iniciar_flujo_apertura(
            numero_partida=gestor.siguiente_numero,
            exportar_archivo=False,
            imprimir_reportes=True,
        )
        if not pda_ap:
            imprimir_alerta("Apertura cancelada o sin cuentas registradas.")
            return None
        fecha = pedir_fecha("\nFecha del asiento de apertura en el Libro Diario [Hoy]: ")

    partida_diario = de_partida_apertura(pda_ap, fecha=fecha, numero=gestor.siguiente_numero)
    return guardar_y_mostrar_partida(gestor, partida_diario)


def registrar_nomina_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Genera y registra la partida de sueldos desde el módulo de planilla."""
    imprimir_banner("REGISTRO DE PARTIDA DE SUELDOS Y SALARIOS", border_style="cyan")
    console.print("  [bold cyan][1][/bold cyan] Generar nómina de ejemplo (Administración y Ventas)")
    console.print("  [bold cyan][2][/bold cyan] Ingresar empleado manualmente")
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
    return guardar_y_mostrar_partida(gestor, partida_diario, "Partida de nómina registrada exitosamente")
