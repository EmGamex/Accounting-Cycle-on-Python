"""Catálogo Contable Central y Motor de Navegación Jerárquica.

Proporciona la estructura contable formal, nomenclatura compatible con NIIF para PYMES
y legislación guatemalteca (SAT / IGSS / Código de Trabajo), así como funciones de navegación.
"""
from typing import Dict, List, Optional, Tuple

catalogo_cuentas: Dict[str, Dict[str, Dict[str, str]]] = {
    "1. Activo": {
        "1.1 Activo Corriente": {
            "1101": "Caja General",
            "1102": "Bancos (Moneda Nacional)",
            "1103": "Cuentas por Cobrar Clientes",
            "1103-R": "(-) Estimación para Cuentas Incobrables",
            "1104": "Inventario de Mercancías",
            "1105": "Material de Empaque",
            "1106": "Moneda Extranjera",
            "1107": "Crédito Fiscal",
            "1108": "Combustibles y Lubricantes",
            "1109": "Caja Chica",
            "1110": "Anticipos a Proveedores",
            "1111": "Anticipos sobre Sueldos a Empleados",
            "1112": "Alquileres Pagados por Anticipado",
            "1113": "Seguros Pagados por Anticipado",
        },
        "1.2 Activo No Corriente": {
            "1201": "Terrenos",
            "1202": "Edificios",
            "1203": "Maquinaria y Equipo",
            "1204": "Mobiliario y Equipo de Oficina",
            "1205": "(-) Depreciación Acumulada",
            "1205-01": "(-) Depreciación Acumulada Edificios",
            "1205-02": "(-) Depreciación Acumulada Maquinaria",
            "1205-03": "(-) Depreciación Acumulada Mobiliario y Equipo",
            "1205-04": "(-) Depreciación Acumulada Vehículos",
            "1206": "Vehículos",
            "1207": "Documentos por Cobrar a Largo Plazo",
            "1208": "Herramientas",
            "1209": "Marcas y Patentes",
            "1210": "(-) Amortización Acumulada",
        },
    },
    "2. Pasivo": {
        "2.1 Pasivo Corriente": {
            "2101": "Proveedores Locales",
            "2102": "Cuentas por Pagar a Corto Plazo",
            "2103": "Impuestos por Pagar",
            "2104": "Sueldos y Salarios Retenidos",
            "2104-01": "Cuotas IGSS por Pagar (Laboral + Patronal)",
            "2104-02": "Retención ISR Sueldos por Pagar",
            "2104-03": "Retención ISR Compras y Servicios por Pagar",
            "2104-04": "Sueldos y Salarios por Pagar",
            "2104-05": "Otras Retenciones por Pagar",
            "2105": "IVA por Pagar",
            "2106": "Acreedores",
            "2107": "Intereses por Pagar",
            "2108": "Provisiones para Prestaciones Laborales (Aguinaldo, Bono 14, Vacaciones)",
        },
        "2.2 Pasivo No Corriente": {
            "2201": "Acreedores Hipotecarios",
            "2202": "Préstamos Bancarios a Largo Plazo",
            "2203": "Documentos por Pagar a Largo Plazo",
            "2204": "Hipotecas",
            "2205": "Reserva para Indemnizaciones Laborales",
        },
    },
    "3. Capital / Patrimonio": {
        "3.1 Capital Contable": {
            "3101": "Capital Social",
            "3102": "Reserva Legal",
            "3103": "Utilidades Acumuladas de Ejercicios Anteriores",
            "3104": "(-) Pérdidas Acumuladas",
            "3105": "Resultado del Ejercicio",
        },
    },
    "4. Ingresos": {
        "4.1 Ingresos Ordinarios": {
            "4101": "Ventas de Mercancías",
            "4102": "Prestación de Servicios",
            "4103": "(-) Devoluciones y Rebajas sobre Ventas",
        },
        "4.2 Ingresos Extraordinarios": {
            "4201": "Otros Ingresos",
            "4202": "Productos Financieros (Intereses Ganados)",
            "4203": "Diferenciales Cambiarios",
        },
    },
    "5. Costos y Gastos": {
        "5.1 Costos": {
            "5101": "Costo de Ventas",
            "5102": "Compras de Materia Prima",
            "5103": "Gastos sobre Compras",
        },
        "5.2 Gastos de Operación": {
            "5201": "Gastos de Administración (Sueldos, Luz, Agua)",
            "5201-01": "Sueldos de Administración",
            "5201-02": "Bonificación Incentivo Administración",
            "5201-03": "Cuota Patronal Administración",
            "5201-04": "Sueldos Extraordinarios Administración",
            "5201-05": "Prestaciones Laborales Administración",
            "5202": "Gastos de Venta (Publicidad, Comisiones)",
            "5202-01": "Sueldos de Ventas",
            "5202-02": "Bonificación Incentivo Ventas",
            "5202-03": "Comisiones sobre Ventas",
            "5202-04": "Cuota Patronal Ventas",
            "5202-05": "Sueldos Extraordinarios Ventas",
            "5202-06": "Prestaciones Laborales Ventas",
            "5202-07": "Publicidad y Propaganda",
            "5203": "Gastos Financieros (Intereses Pagados, Comisiones Bancarias)",
            "5203-01": "Intereses Pagados",
            "5203-02": "Comisiones Bancarias",
        },
    },
}


# --- LÓGICA DE NAVEGACIÓN Y CONSULTA ---

def listar_clases() -> List[str]:
    """Retorna las clases principales del catálogo (Activo, Pasivo, etc.)."""
    return list(catalogo_cuentas.keys())


def listar_subgrupos(clase: Optional[str] = None) -> Dict[str, List[str]]:
    """Retorna los subgrupos agrupados por clase o para una clase específica."""
    resultado: Dict[str, List[str]] = {}
    for c, subgrupos in catalogo_cuentas.items():
        if clase is None or clase.lower() in c.lower():
            resultado[c] = list(subgrupos.keys())
    return resultado


def listar_cuentas(filtro_clase: Optional[str] = None) -> List[Tuple[str, str, str, str]]:
    """Retorna una lista plana de tuplas: (clase, subgrupo, codigo, nombre)."""
    cuentas: List[Tuple[str, str, str, str]] = []
    for clase, subgrupos in catalogo_cuentas.items():
        if filtro_clase and filtro_clase.lower() not in clase.lower():
            continue
        for subgrupo, items in subgrupos.items():
            for codigo, nombre in items.items():
                cuentas.append((clase, subgrupo, codigo, nombre))
    return cuentas


def buscar_cuenta(termino: str) -> List[Tuple[str, str, str, str]]:
    """Busca cuentas por coincidencia en código o en nombre."""
    termino_clean = termino.strip().lower()
    coincidencias: List[Tuple[str, str, str, str]] = []
    for clase, subgrupo, codigo, nombre in listar_cuentas():
        if termino_clean == codigo.lower() or termino_clean in nombre.lower():
            coincidencias.append((clase, subgrupo, codigo, nombre))
    return coincidencias


def imprimir_arbol_catalogo() -> None:
    """Imprime el árbol jerárquico contable formateado en consola."""
    print("=" * 75)
    print("           CATÁLOGO CONTABLE JERÁRQUICO DE CUENTAS")
    print("=" * 75)
    for clase, subgrupos in catalogo_cuentas.items():
        print(f"\n[{clase.upper()}]")
        for subgrupo, cuentas in subgrupos.items():
            print(f"  └─ {subgrupo}")
            for codigo, nombre in cuentas.items():
                print(f"       {codigo:<9} │ {nombre}")
    print("\n" + "=" * 75)


if __name__ == "__main__":
    imprimir_arbol_catalogo()
