"""Catálogo Contable Central y Motor de Navegación Jerárquica.

Proporciona la estructura contable formal, nomenclatura compatible con NIIF para PYMES
y legislación guatemalteca (SAT / IGSS / Código de Trabajo), así como funciones de navegación.
"""
import difflib
import re
import sys
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Polyfill de StrEnum para compatibilidad con Python < 3.11."""
        def __str__(self) -> str:
            return str(self.value)


@dataclass
class CuentaCatalogo:
    """Modelo canónico de una cuenta en el catálogo contable."""
    codigo: str
    nombre: str
    nombre_norm: str
    clase: str
    subgrupo: str
    es_regularizadora: bool = False

    def __iter__(self) -> Iterator[str]:
        """Permite desempaquetado directo como 4-tupla: (clase, subgrupo, codigo, nombre)."""
        yield self.clase
        yield self.subgrupo
        yield self.codigo
        yield self.nombre

    def __getitem__(self, idx: int) -> str:
        """Compatibilidad con acceso por índice como tupla (0: clase, 1: subgrupo, 2: codigo, 3: nombre)."""
        mapeo = (self.clase, self.subgrupo, self.codigo, self.nombre)
        return mapeo[idx]

    def __len__(self) -> int:
        return 4


PATRONES_REGULARIZADORAS = [
    "depreciacion acumulada",
    "amortizacion acumulada",
    "estimacion para",
    "reserva para",
    "perdidas acumuladas",
    "deterioro",
]

SINONIMOS = {
    "mercaderia": "inventario de mercancias",
    "mercaderias": "inventario de mercancias",
    "mercancia": "inventario de mercancias",
    "inventario": "inventario de mercancias",
    "banco": "bancos",
    "prestamo": "prestamos bancarios",
    "prestamos": "prestamos bancarios",
    "mobiliario": "mobiliario y equipo",
    "equipo de oficina": "mobiliario y equipo de oficina",
    "capital": "capital social",
    "depreciacion": "depreciacion acumulada",
    "vehiculo": "vehiculos",
    "letra": "documentos por cobrar a corto plazo",
    "letras": "documentos por cobrar a corto plazo",
    "letras de cambio": "documentos por cobrar a corto plazo",
    "documentos por cobrar": "documentos por cobrar a corto plazo",
    "documentos por pagar": "documentos por pagar a corto plazo",
    "letras por pagar": "documentos por pagar a corto plazo",
    "letras por cobrar": "documentos por cobrar a corto plazo",
    "pagare": "documentos por cobrar a corto plazo",
    "pagares": "documentos por cobrar a corto plazo",
}


def normalizar(texto: str) -> str:
    """Elimina tildes, caracteres especiales y convierte a minúsculas."""
    if not texto:
        return ""
    texto_norm = unicodedata.normalize("NFD", texto)
    limpio = "".join(c for c in texto_norm if unicodedata.category(c) != "Mn").lower().strip()
    return re.sub(r"^[(\-)\s]+", "", limpio)


def es_cuenta_regularizadora(nombre: str) -> bool:
    """Detecta si una cuenta contable es regularizadora/complementaria de saldo contrario."""
    norm = normalizar(nombre)
    return any(p in norm for p in PATRONES_REGULARIZADORAS) or "(-)" in nombre


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
    DOCS_COBRAR_CP = "1114"

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
    DOCS_POR_PAGAR_CP = "2109"

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
            Cuenta.DOCS_COBRAR_CP: "Documentos por Cobrar a Corto Plazo",
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
            Cuenta.DOCS_POR_PAGAR_CP: "Documentos por Pagar a Corto Plazo",
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


class CatalogoService:
    """Servicio con indexación O(1) en memoria para búsquedas eficientes en catálogo."""

    def __init__(
        self,
        catalogo_dict: Optional[dict] = None,
        filtro_clases: Optional[Iterable[str]] = None,
    ):
        self._por_codigo: Dict[str, CuentaCatalogo] = {}
        self._por_nombre_norm: Dict[str, CuentaCatalogo] = {}
        self._cuentas: List[CuentaCatalogo] = []
        self._nombres_norm: List[str] = []
        self._filtro_clases = list(filtro_clases) if filtro_clases else None

        fuente = catalogo_dict if catalogo_dict is not None else catalogo_cuentas
        self._indexar(fuente)

    @classmethod
    def desde_modulo(cls, filtro_clases: Optional[Iterable[str]] = None) -> "CatalogoService":
        """Carga e indexa el catálogo central."""
        return cls(catalogo_cuentas, filtro_clases=filtro_clases)

    def _indexar(self, catalogo: dict) -> None:
        """Construye índices O(1) a partir de la estructura jerárquica contable."""
        self._por_codigo.clear()
        self._por_nombre_norm.clear()
        self._cuentas.clear()
        self._nombres_norm.clear()

        for clase, subgrupos in catalogo.items():
            if self._filtro_clases and not any(k.lower() in clase.lower() for k in self._filtro_clases):
                continue

            for subgrupo, cuentas in subgrupos.items():
                for codigo, nombre in cuentas.items():
                    cod_str = str(codigo).strip()
                    norm = normalizar(nombre)
                    es_reg = es_cuenta_regularizadora(nombre)

                    item = CuentaCatalogo(
                        codigo=cod_str,
                        nombre=nombre,
                        nombre_norm=norm,
                        clase=clase,
                        subgrupo=subgrupo,
                        es_regularizadora=es_reg,
                    )

                    self._cuentas.append(item)
                    self._por_codigo[cod_str] = item
                    if norm not in self._por_nombre_norm:
                        self._por_nombre_norm[norm] = item
                    self._nombres_norm.append(norm)

    @property
    def cuentas(self) -> List[CuentaCatalogo]:
        return list(self._cuentas)

    def buscar(self, texto_usuario: str) -> Optional[CuentaCatalogo]:
        """Búsqueda eficiente: O(1) por código o nombre exacto/sinónimo, seguida de tokens y difflib."""
        texto_limpio = texto_usuario.strip()
        if not texto_limpio:
            return None

        if texto_limpio in self._por_codigo:
            return self._por_codigo[texto_limpio]

        texto_norm = normalizar(texto_limpio)
        termino = SINONIMOS.get(texto_norm, texto_norm)

        if texto_norm in self._por_nombre_norm:
            return self._por_nombre_norm[texto_norm]
        if termino in self._por_nombre_norm:
            return self._por_nombre_norm[termino]

        terminos_busqueda = [termino]
        if texto_norm != termino:
            terminos_busqueda.append(texto_norm)

        for obj in terminos_busqueda:
            candidatos = []
            if len(obj) >= 4:
                candidatos = [c for c in self._cuentas if obj in c.nombre_norm]
            else:
                patron = rf"\b{re.escape(obj)}\b"
                candidatos = [c for c in self._cuentas if re.search(patron, c.nombre_norm)]

            if candidatos:
                busca_reg = any(r in obj for r in PATRONES_REGULARIZADORAS)
                candidatos.sort(key=lambda c: (c.es_regularizadora if not busca_reg else not c.es_regularizadora, len(c.nombre_norm)))
                return candidatos[0]

        # 4. Todas las palabras contenidas
        palabras = termino.split()
        if len(palabras) > 1:
            coincidencias_palabras = [c for c in self._cuentas if all(p in c.nombre_norm for p in palabras)]
            if coincidencias_palabras:
                coincidencias_palabras.sort(key=lambda c: len(c.nombre_norm))
                return coincidencias_palabras[0]

        # 5. Similitud difusa con difflib
        coincidencias = difflib.get_close_matches(termino, self._nombres_norm, n=1, cutoff=0.55)
        if not coincidencias and texto_norm != termino:
            coincidencias = difflib.get_close_matches(texto_norm, self._nombres_norm, n=1, cutoff=0.55)

        if coincidencias:
            return self._por_nombre_norm.get(coincidencias[0])

        return None

    def buscar_coincidencias(self, texto_usuario: str) -> List[CuentaCatalogo]:
        """Busca todas las cuentas que coincidan por código o nombre para selección interactiva."""
        texto_limpio = texto_usuario.strip()
        if not texto_limpio:
            return []

        # 1. Búsqueda exacta por código
        if texto_limpio in self._por_codigo:
            return [self._por_codigo[texto_limpio]]

        texto_norm = normalizar(texto_limpio)
        termino = SINONIMOS.get(texto_norm, texto_norm)

        coincidencias: List[CuentaCatalogo] = []
        codigos_vistos = set()

        def agregar(c: CuentaCatalogo):
            if c.codigo not in codigos_vistos:
                codigos_vistos.add(c.codigo)
                coincidencias.append(c)

        # 2. Coincidencia exacta por nombre normalizado o sinónimo
        if texto_norm in self._por_nombre_norm:
            agregar(self._por_nombre_norm[texto_norm])
        if termino in self._por_nombre_norm:
            agregar(self._por_nombre_norm[termino])

        # 3. Subcadena en código o nombre
        termino_lower = texto_limpio.lower()
        for c in self._cuentas:
            if (
                termino_lower in c.codigo.lower()
                or termino in c.nombre_norm
                or texto_norm in c.nombre_norm
            ):
                agregar(c)

        # 4. Palabras contenidas
        palabras = termino.split()
        if len(palabras) > 1:
            for c in self._cuentas:
                if all(p in c.nombre_norm for p in palabras):
                    agregar(c)

        # 5. Similitud difusa con difflib si no hay coincidencias directas
        if not coincidencias:
            cercanas = difflib.get_close_matches(termino, self._nombres_norm, n=5, cutoff=0.50)
            for nombre_cercano in cercanas:
                if nombre_cercano in self._por_nombre_norm:
                    agregar(self._por_nombre_norm[nombre_cercano])

        return coincidencias


_CATALOGO_SERVICIO_GLOBAL: Optional[CatalogoService] = None


def obtener_catalogo_servicio() -> CatalogoService:
    """Retorna la instancia global única del servicio de catálogo indexado."""
    global _CATALOGO_SERVICIO_GLOBAL
    if _CATALOGO_SERVICIO_GLOBAL is None:
        _CATALOGO_SERVICIO_GLOBAL = CatalogoService.desde_modulo()
    return _CATALOGO_SERVICIO_GLOBAL


def buscar_cuenta(termino: str) -> List[CuentaCatalogo]:
    """Busca cuentas por coincidencia en código o en nombre (soporta acceso como 4-tupla o CuentaCatalogo)."""
    return obtener_catalogo_servicio().buscar_coincidencias(termino)


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