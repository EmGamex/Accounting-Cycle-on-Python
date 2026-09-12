"""Manejadores de entrada/salida (Consola interactiva, formateo de boletas y CSV)."""
import csv
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple

from ui import console, imprimir_alerta, imprimir_banner
from .config import money
from .models import DatosEmpleado, PartidaContable, ResultadoPlanilla


def leer_decimal(mensaje: str, default: Optional[Decimal] = Decimal("0.00")) -> Optional[Decimal]:
    """Solicita un valor numérico por consola y lo convierte de forma segura a Decimal."""
    sufijo = f"[{default:.2f}]" if default is not None else "[Enter para auto]"
    entrada = input(f"{mensaje} {sufijo}: ").strip().replace(",", "")

    if not entrada:
        return default
    try:
        return money(Decimal(entrada))
    except (InvalidOperation, ValueError):
        imprimir_alerta("Valor numérico no válido. Se usará el valor por defecto.")
        return default


def solicitar_datos_interactivo() -> DatosEmpleado:
    """Captura interactiva de un empleado desde la consola."""
    imprimir_banner("DATOS DEL EMPLEADO", border_style="cyan")

    nombre = input("Nombre completo: ").strip() or "Empleado General"

    print("Departamento:")
    print("  [1] Administración (por defecto)")
    print("  [2] Ventas")
    opcion_depto = input("Seleccione departamento [1]: ").strip()
    if opcion_depto == "2":
        departamento = "Ventas"
    elif opcion_depto and opcion_depto not in ("1", ""):
        departamento = opcion_depto.strip().title()
    else:
        departamento = "Administración"

    sueldo_base = leer_decimal("Sueldo Base mensual (Q)", default=Decimal("0.00")) or Decimal("0.00")
    ventas = leer_decimal("Ventas del mes (Q)", default=Decimal("0.00")) or Decimal("0.00")
    pct_comision = (
        leer_decimal("Porcentaje de comisión (%)", default=Decimal("0.00"))
        if ventas > Decimal("0.00")
        else Decimal("0.00")
    ) or Decimal("0.00")

    horas_extras = leer_decimal("Horas extras trabajadas", default=Decimal("0.00")) or Decimal("0.00")
    prestamos = leer_decimal("Anticipo sobre sueldos (Q)", default=Decimal("0.00")) or Decimal("0.00")
    otros_desc = leer_decimal("Deudores empleados / Otros (Q)", default=Decimal("0.00")) or Decimal("0.00")
    isr_manual = leer_decimal("Retención ISR fija (Q)", default=None)

    return DatosEmpleado(
        nombre=nombre,
        departamento=departamento,
        sueldo_base=sueldo_base,
        ventas=ventas,
        pct_comision=pct_comision,
        horas_extras=horas_extras,
        prestamos_deudas=prestamos,
        otros_descuentos=otros_desc,
        isr_manual=isr_manual,
    )


def imprimir_boleta(r: ResultadoPlanilla) -> None:
    """Muestra en pantalla la boleta individual de pago con Rich (delega a ui.tablas)."""
    from ui import console
    from ui.tablas import generar_tabla_boleta

    tabla = generar_tabla_boleta(r)
    console.print(tabla)


def imprimir_partida(p: PartidaContable) -> None:
    """Muestra en pantalla el asiento contable en partida doble con Rich (delega a ui.tablas)."""
    from ui import console, imprimir_alerta, imprimir_exito
    from ui.tablas import generar_tabla_partida_nomina

    tabla = generar_tabla_partida_nomina(p)
    console.print(tabla)
    if p.cuadra:
        imprimir_exito("La partida cuadra exactamente al centavo.")
    else:
        imprimir_alerta(f"Discrepancia detectada: Q{p.diferencia:,.2f}")


# ----------------------------------------------------------------------
# Funciones preparadas para integración y uso futuro con archivos CSV
# ----------------------------------------------------------------------

def cargar_empleados_csv(ruta_csv: str) -> List[DatosEmpleado]:
    """Carga una lista de empleados desde un archivo CSV."""
    empleados: List[DatosEmpleado] = []
    with open(ruta_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for fila in reader:
            if not fila.get("nombre"):
                continue
            isr = fila.get("isr_manual", "").strip()
            empleados.append(
                DatosEmpleado(
                    nombre=fila["nombre"].strip(),
                    departamento=fila.get("departamento", "Administración").strip() or "Administración",
                    sueldo_base=money(fila.get("sueldo_base", "0.00")),
                    ventas=money(fila.get("ventas", "0.00")),
                    pct_comision=money(fila.get("pct_comision", "0.00")),
                    horas_extras=money(fila.get("horas_extras", "0.00")),
                    prestamos_deudas=money(fila.get("prestamos_deudas", "0.00")),
                    otros_descuentos=money(fila.get("otros_descuentos", "0.00")),
                    isr_manual=money(isr) if isr else None,
                    jornada_horas=money(fila.get("jornada_horas", "8.0")),
                )
            )
    return empleados


def exportar_planilla_csv(resultados: List[ResultadoPlanilla], ruta_csv: str) -> None:
    """Exporta el reporte de planilla consolidado a un archivo CSV."""
    if not resultados:
        return
    columnas = [
        "empleado",
        "departamento",
        "sueldo_base",
        "comisiones",
        "horas_extras_trabajadas",
        "sueldo_extraordinario",
        "bonificacion_ley",
        "total_afecto_igss",
        "total_devengado",
        "descuento_igss",
        "descuento_isr",
        "prestamos_deudas",
        "otros_descuentos",
        "total_descuentos",
        "liquido_recibir",
    ]
    with open(ruta_csv, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for r in resultados:
            writer.writerow({k: str(getattr(r, k)) for k in columnas})


def crear_plantilla_csv_ejemplo(ruta_csv: str) -> None:
    """Genera una plantilla CSV vacía/ejemplo lista para ser rellenada."""
    campos = [
        "nombre",
        "departamento",
        "sueldo_base",
        "ventas",
        "pct_comision",
        "horas_extras",
        "prestamos_deudas",
        "otros_descuentos",
        "isr_manual",
        "jornada_horas",
    ]
    filas_ejemplo = [
        {
            "nombre": "Juan Pérez",
            "departamento": "Administración",
            "sueldo_base": "4500.00",
            "ventas": "0.00",
            "pct_comision": "0.00",
            "horas_extras": "5.0",
            "prestamos_deudas": "200.00",
            "otros_descuentos": "0.00",
            "isr_manual": "",
            "jornada_horas": "8.0",
        },
        {
            "nombre": "Ana Gómez",
            "departamento": "Ventas",
            "sueldo_base": "3500.00",
            "ventas": "25000.00",
            "pct_comision": "3.00",
            "horas_extras": "0.0",
            "prestamos_deudas": "0.00",
            "otros_descuentos": "50.00",
            "isr_manual": "",
            "jornada_horas": "8.0",
        },
    ]
    with open(ruta_csv, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas_ejemplo)
