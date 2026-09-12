"""Catálogo Contable Central y Motor de Navegación Jerárquica.

Proporciona la estructura contable formal, nomenclatura compatible con NIIF para PYMES
y legislación guatemalteca (SAT / IGSS / Código de Trabajo), así como funciones de navegación.
"""
from enum import StrEnum
from typing import Dict, List, Optional, Tuple


class Cuenta(StrEnum):
    """Identificadores canónicos de cuentas contables estándar del sistema."""
    # 1.1 Activo Corriente
    CAJA = "1101"
    BANCOS = "1102"
    CLIENTES = "1103"
    ESTIMACION_INCOBRABLES = "1103-R"
    MERCADERIAS = "1104"
    MATERIAL_EMPAQUE = "1105"
    MONEDA_EXTRANJERA = "1106"
    IVA_CREDITO = "1107"
    COMBUSTIBLES = "1108"
    CAJA_CHICA = "1109"
    ANTICIPOS_PROVEEDORES = "1110"
    ANTICIPOS_SUELDOS = "1111"
    ALQUILERES_ANTICIPADOS = "1112"
    SEGUROS_ANTICIPADOS = "1113"

    # 1.2 Activo No Corriente
    TERRENOS = "1201"
    EDIFICIOS = "1202"
    MAQUINARIA = "1203"
    MOBILIARIO = "1204"
    DEPREC_ACUMULADA = "1205"
    DEPREC_ACUM_EDIFICIOS = "1205-01"
    DEPREC_ACUM_MAQUINARIA = "1205-02"
    DEPREC_ACUM_MOBILIARIO = "1205-03"
    DEPREC_ACUM_VEHICULOS = "1205-04"
    VEHICULOS = "1206"
    DOCS_COBRAR_LP = "1207"
    HERRAMIENTAS = "1208"
    MARCAS_PATENTES = "1209"
    AMORT_ACUMULADA = "1210"

    # 2.1 Pasivo Corriente
    PROVEEDORES = "2101"
    CUENTAS_POR_PAGAR_CP = "2102"
    IMPUESTOS_POR_PAGAR = "2103"
    SUELDOS_RETENIDOS = "2104"
    IGSS_POR_PAGAR = "2104-01"
    RETENCION_ISR_SUELDOS = "2104-02"
    RETENCION_ISR_COMPRAS = "2104-03"
    SUELDOS_POR_PAGAR = "2104-04"
    OTRAS_RETENCIONES = "2104-05"
    IVA_DEBITO = "2105"
    ACREEDORES = "2106"
    INTERESES_POR_PAGAR = "2107"
    PROVISIONES_LABORALES = "2108"

    # 2.2 Pasivo No Corriente
    ACREEDORES_HIPOTECARIOS = "2201"
    PRESTAMOS_BANCARIOS = "2202"
    DOCS_POR_PAGAR_LP = "2203"
    HIPOTECAS = "2204"
    RESERVA_INDEMNIZACIONES = "2205"

    # 3. Capital / Patrimonio
    CAPITAL_SOCIAL = "3101"
    RESERVA_LEGAL = "3102"
    UTILIDADES_ACUMULADAS = "3103"
    PERDIDAS_ACUMULADAS = "3104"
    RESULTADO_EJERCICIO = "3105"

    # 4. Ingresos
    VENTAS = "4101"
    SERVICIOS = "4102"
    DEVOLUCIONES_VENTAS = "4103"
    OTROS_INGRESOS = "4201"
    PRODUCTOS_FINANCIEROS = "4202"
    DIFERENCIAL_CAMBIARIO = "4203"

    # 5. Costos y Gastos
    COSTO_VENTAS = "5101"
    COMPRAS = "5102"
    GASTOS_SOBRE_COMPRAS = "5103"
    GASTOS_ADMIN = "5201"
    SUELDOS_ADMIN = "5201-01"
    BONIFICACION_ADMIN = "5201-02"
    CUOTA_PATRONAL_ADMIN = "5201-03"
    SUELDOS_EXTRA_ADMIN = "5201-04"
    PRESTACIONES_ADMIN = "5201-05"
    GASTOS_VENTAS = "5202"
    SUELDOS_VENTAS = "5202-01"
    BONIFICACION_VENTAS = "5202-02"
    COMISIONES_VENTAS = "5202-03"
    CUOTA_PATRONAL_VENTAS = "5202-04"
    SUELDOS_EXTRA_VENTAS = "5202-05"
    PRESTACIONES_VENTAS = "5202-06"
    PUBLICIDAD = "5202-07"
    GASTOS_FINANCIEROS = "5203"
    INTERESES_PAGADOS = "5203-01"
    COMISIONES_BANCARIAS = "5203-02"


catalogo_cuentas: Dict[str, Dict[str, Dict[str, str]]] = {
    "1. Activo": {
        "1.1 Activo Corriente": {
            Cuenta.CAJA: "Caja General",
            Cuenta.BANCOS: "Bancos (Moneda Nacional)",
            Cuenta.CLIENTES: "Cuentas por Cobrar Clientes",
            Cuenta.ESTIMACION_INCOBRABLES: "(-) Estimación para Cuentas Incobrables",
            Cuenta.MERCADERIAS: "Inventario de Mercancías",
            Cuenta.MATERIAL_EMPAQUE: "Material de Empaque",
            Cuenta.MONEDA_EXTRANJERA: "Moneda Extranjera",
            Cuenta.IVA_CREDITO: "Crédito Fiscal",
            Cuenta.COMBUSTIBLES: "Combustibles y Lubricantes",
            Cuenta.CAJA_CHICA: "Caja Chica",
            Cuenta.ANTICIPOS_PROVEEDORES: "Anticipos a Proveedores",
            Cuenta.ANTICIPOS_SUELDOS: "Anticipos sobre Sueldos a Empleados",
            Cuenta.ALQUILERES_ANTICIPADOS: "Alquileres Pagados por Anticipado",
            Cuenta.SEGUROS_ANTICIPADOS: "Seguros Pagados por Anticipado",
        },
        "1.2 Activo No Corriente": {
            Cuenta.TERRENOS: "Terrenos",
            Cuenta.EDIFICIOS: "Edificios",
            Cuenta.MAQUINARIA: "Maquinaria y Equipo",
            Cuenta.MOBILIARIO: "Mobiliario y Equipo de Oficina",
            Cuenta.DEPREC_ACUMULADA: "(-) Depreciación Acumulada",
            Cuenta.DEPREC_ACUM_EDIFICIOS: "(-) Depreciación Acumulada Edificios",
            Cuenta.DEPREC_ACUM_MAQUINARIA: "(-) Depreciación Acumulada Maquinaria",
            Cuenta.DEPREC_ACUM_MOBILIARIO: "(-) Depreciación Acumulada Mobiliario y Equipo",
            Cuenta.DEPREC_ACUM_VEHICULOS: "(-) Depreciación Acumulada Vehículos",
            Cuenta.VEHICULOS: "Vehículos",
            Cuenta.DOCS_COBRAR_LP: "Documentos por Cobrar a Largo Plazo",
            Cuenta.HERRAMIENTAS: "Herramientas",
            Cuenta.MARCAS_PATENTES: "Marcas y Patentes",
            Cuenta.AMORT_ACUMULADA: "(-) Amortización Acumulada",
        },
    },
    "2. Pasivo": {
        "2.1 Pasivo Corriente": {
            Cuenta.PROVEEDORES: "Proveedores Locales",
            Cuenta.CUENTAS_POR_PAGAR_CP: "Cuentas por Pagar a Corto Plazo",
            Cuenta.IMPUESTOS_POR_PAGAR: "Impuestos por Pagar",
            Cuenta.SUELDOS_RETENIDOS: "Sueldos y Salarios Retenidos",
            Cuenta.IGSS_POR_PAGAR: "Cuotas IGSS por Pagar (Laboral + Patronal)",
            Cuenta.RETENCION_ISR_SUELDOS: "Retención ISR Sueldos por Pagar",
            Cuenta.RETENCION_ISR_COMPRAS: "Retención ISR Compras y Servicios por Pagar",
            Cuenta.SUELDOS_POR_PAGAR: "Sueldos y Salarios por Pagar",
            Cuenta.OTRAS_RETENCIONES: "Otras Retenciones por Pagar",
            Cuenta.IVA_DEBITO: "IVA por Pagar",
            Cuenta.ACREEDORES: "Acreedores",
            Cuenta.INTERESES_POR_PAGAR: "Intereses por Pagar",
            Cuenta.PROVISIONES_LABORALES: "Provisiones para Prestaciones Laborales (Aguinaldo, Bono 14, Vacaciones)",
        },
        "2.2 Pasivo No Corriente": {
            Cuenta.ACREEDORES_HIPOTECARIOS: "Acreedores Hipotecarios",
            Cuenta.PRESTAMOS_BANCARIOS: "Préstamos Bancarios a Largo Plazo",
            Cuenta.DOCS_POR_PAGAR_LP: "Documentos por Pagar a Largo Plazo",
            Cuenta.HIPOTECAS: "Hipotecas",
            Cuenta.RESERVA_INDEMNIZACIONES: "Reserva para Indemnizaciones Laborales",
        },
    },
    "3. Capital / Patrimonio": {
        "3.1 Capital Contable": {
            Cuenta.CAPITAL_SOCIAL: "Capital Social",
            Cuenta.RESERVA_LEGAL: "Reserva Legal",
            Cuenta.UTILIDADES_ACUMULADAS: "Utilidades Acumuladas de Ejercicios Anteriores",
            Cuenta.PERDIDAS_ACUMULADAS: "(-) Pérdidas Acumuladas",
            Cuenta.RESULTADO_EJERCICIO: "Resultado del Ejercicio",
        },
    },
    "4. Ingresos": {
        "4.1 Ingresos Ordinarios": {
            Cuenta.VENTAS: "Ventas de Mercancías",
            Cuenta.SERVICIOS: "Prestación de Servicios",
            Cuenta.DEVOLUCIONES_VENTAS: "(-) Devoluciones y Rebajas sobre Ventas",
        },
        "4.2 Ingresos Extraordinarios": {
            Cuenta.OTROS_INGRESOS: "Otros Ingresos",
            Cuenta.PRODUCTOS_FINANCIEROS: "Productos Financieros (Intereses Ganados)",
            Cuenta.DIFERENCIAL_CAMBIARIO: "Diferenciales Cambiarios",
        },
    },
    "5. Costos y Gastos": {
        "5.1 Costos": {
            Cuenta.COSTO_VENTAS: "Costo de Ventas",
            Cuenta.COMPRAS: "Compras de Materia Prima",
            Cuenta.GASTOS_SOBRE_COMPRAS: "Gastos sobre Compras",
        },
        "5.2 Gastos de Operación": {
            Cuenta.GASTOS_ADMIN: "Gastos de Administración (Sueldos, Luz, Agua)",
            Cuenta.SUELDOS_ADMIN: "Sueldos de Administración",
            Cuenta.BONIFICACION_ADMIN: "Bonificación Incentivo Administración",
            Cuenta.CUOTA_PATRONAL_ADMIN: "Cuota Patronal Administración",
            Cuenta.SUELDOS_EXTRA_ADMIN: "Sueldos Extraordinarios Administración",
            Cuenta.PRESTACIONES_ADMIN: "Prestaciones Laborales Administración",
            Cuenta.GASTOS_VENTAS: "Gastos de Venta (Publicidad, Comisiones)",
            Cuenta.SUELDOS_VENTAS: "Sueldos de Ventas",
            Cuenta.BONIFICACION_VENTAS: "Bonificación Incentivo Ventas",
            Cuenta.COMISIONES_VENTAS: "Comisiones sobre Ventas",
            Cuenta.CUOTA_PATRONAL_VENTAS: "Cuota Patronal Ventas",
            Cuenta.SUELDOS_EXTRA_VENTAS: "Sueldos Extraordinarios Ventas",
            Cuenta.PRESTACIONES_VENTAS: "Prestaciones Laborales Ventas",
            Cuenta.PUBLICIDAD: "Publicidad y Propaganda",
            Cuenta.GASTOS_FINANCIEROS: "Gastos Financieros (Intereses Pagados, Comisiones Bancarias)",
            Cuenta.INTERESES_PAGADOS: "Intereses Pagados",
            Cuenta.COMISIONES_BANCARIAS: "Comisiones Bancarias",
        },
    },
}


# --- DICCIONARIO PLANO INDEXADO ---
CUENTAS_PLANAS: Dict[str, str] = {
    codigo: nombre
    for clase in catalogo_cuentas.values()
    for subgrupo in clase.values()
    for codigo, nombre in subgrupo.items()
}


def obtener_nombre_cuenta(codigo: str | Cuenta) -> Optional[str]:
    """Retorna el nombre formal de la cuenta a partir de su código o miembro de Cuenta."""
    cod_str = str(codigo).strip()
    return CUENTAS_PLANAS.get(cod_str)


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
                cuentas.append((clase, subgrupo, str(codigo), nombre))
    return cuentas


def buscar_cuenta(termino: str) -> List[Tuple[str, str, str, str]]:
    """Busca cuentas por coincidencia en código o en nombre."""
    termino_clean = termino.strip().lower()
    coincidencias: List[Tuple[str, str, str, str]] = []
    for clase, subgrupo, codigo, nombre in listar_cuentas():
        if termino_clean == codigo.lower() or termino_clean in nombre.lower():
            coincidencias.append((clase, subgrupo, codigo, nombre))
    return coincidencias


def generar_arbol_rich(filtro_clase: Optional[str] = None):
    """Genera un árbol jerárquico de cuentas contables compatible con Rich (delega a ui.arbol)."""
    from ui.arbol import generar_arbol_catalogo
    return generar_arbol_catalogo(filtro_clase=filtro_clase)


def mostrar_catalogo_rich(filtro_clase: Optional[str] = None, console_obj=None) -> None:
    """Muestra el catálogo contable en consola utilizando Rich Tree (delega a ui.arbol)."""
    try:
        from ui.arbol import mostrar_catalogo_arbol
        mostrar_catalogo_arbol(filtro_clase=filtro_clase, console_obj=console_obj)
    except ImportError:
        imprimir_arbol_catalogo()


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
    mostrar_catalogo_rich()