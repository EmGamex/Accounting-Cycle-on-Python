"""Motor de carga, normalización, indexación y búsqueda del catálogo contable."""
import difflib
import importlib
import re
import unicodedata
from typing import Dict, List, Optional

from apertura.models import CuentaCatalogo

PATRONES_REGULARIZADORAS = [
    "depreciacion acumulada",
    "amortizacion acumulada",
    "estimacion para",
    "reserva para",
    "perdidas acumuladas",
    "deterioro",
]

SINONIMOS = {
    "mercaderia": "mercancias",
    "mercaderias": "mercancias",
    "mercancia": "mercancias",
    "inventario": "inventario de mercancias",
    "banco": "bancos",
    "prestamo": "prestamos bancarios",
    "prestamos": "prestamos bancarios",
    "mobiliario": "mobiliario y equipo",
    "equipo de oficina": "mobiliario y equipo de oficina",
    "capital": "capital social",
    "depreciacion": "depreciacion acumulada",
    "vehiculo": "vehiculos",
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


class CatalogoService:
    """Servicio con indexación O(1) en memoria para búsquedas eficientes en catálogo."""

    def __init__(self, catalogo_dict: Optional[dict] = None):
        self._por_codigo: Dict[str, CuentaCatalogo] = {}
        self._por_nombre_norm: Dict[str, CuentaCatalogo] = {}
        self._cuentas: List[CuentaCatalogo] = []
        self._nombres_norm: List[str] = []

        if catalogo_dict is not None:
            self._indexar(catalogo_dict)

    @classmethod
    def desde_modulo(cls) -> "CatalogoService":
        """Carga e indexa el catálogo importando dinámicamente el módulo disponible."""
        dict_catalogo = None
        try:
            modulo = importlib.import_module("catalogo_contable")
            if hasattr(modulo, "catalogo_cuentas"):
                dict_catalogo = modulo.catalogo_cuentas
        except ModuleNotFoundError:
            dict_catalogo = None

        if dict_catalogo is None:
            raise RuntimeError(
                "No se encontró el módulo del catálogo contable ('catalogo_contable.py')."
            )

        return cls(dict_catalogo)

    def _indexar(self, catalogo: dict) -> None:
        """Construye índices O(1) a partir de la estructura jerárquica contable."""
        self._por_codigo.clear()
        self._por_nombre_norm.clear()
        self._cuentas.clear()
        self._nombres_norm.clear()

        for clase, subgrupos in catalogo.items():
            if not any(k in clase for k in ["Activo", "Pasivo", "Capital", "Patrimonio"]):
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
            for c in self._cuentas:
                if all(p in c.nombre_norm for p in palabras):
                    return c

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

    def obtener_cuenta_capital(self) -> CuentaCatalogo:
        """Localiza la cuenta de capital en el catálogo o retorna una cuenta base estándar."""
        posibles_nombres = ["capital social", "capital contable", "capital", "patrimonio"]
        for c in self._cuentas:
            if c.codigo in ["3101", "3.1.01", "301-01"] or any(p in c.nombre_norm for p in posibles_nombres):
                return c

        return CuentaCatalogo(
            codigo="3101",
            nombre="Capital Social",
            nombre_norm="capital social",
            clase="3. Capital / Patrimonio",
            subgrupo="3.1 Capital Contable",
            es_regularizadora=False,
        )

    @staticmethod
    def crear_cuenta_manual(nombre: str, opcion_clasificacion: str) -> CuentaCatalogo:
        """Crea una cuenta clasificada manualmente cuando no existe en el catálogo."""
        mapa = {
            "1": ("1. Activo", "1.1 Activo Corriente"),
            "2": ("1. Activo", "1.2 Activo No Corriente"),
            "3": ("2. Pasivo", "2.1 Pasivo Corriente"),
            "4": ("2. Pasivo", "2.2 Pasivo No Corriente"),
            "5": ("3. Capital / Patrimonio", "3.1 Capital Contable"),
        }
        clase, subgrupo = mapa.get(opcion_clasificacion, ("1. Activo", "1.1 Activo Corriente"))
        es_reg = es_cuenta_regularizadora(nombre)

        return CuentaCatalogo(
            codigo="S/C",
            nombre=nombre,
            nombre_norm=normalizar(nombre),
            clase=clase,
            subgrupo=subgrupo,
            es_regularizadora=es_reg,
        )
