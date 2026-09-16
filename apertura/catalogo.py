"""Motor de integración de catálogo específico para el balance de apertura contable."""
from typing import Dict, Iterable, List, Optional

from catalogo_contable import (
    PATRONES_REGULARIZADORAS,
    SINONIMOS,
    CatalogoService as BaseCatalogoService,
    CuentaCatalogo,
    es_cuenta_regularizadora,
    normalizar,
)


class CatalogoService(BaseCatalogoService):
    """Servicio de catálogo con especializaciones para el balance de apertura contable."""

    def __init__(
        self,
        catalogo_dict: Optional[dict] = None,
        filtro_clases: Optional[Iterable[str]] = None,
    ):
        # Para apertura, si no se especifica filtro, se filtran las cuentas de balance patrimonial
        clases = filtro_clases if filtro_clases is not None else ("Activo", "Pasivo", "Capital", "Patrimonio")
        super().__init__(catalogo_dict=catalogo_dict, filtro_clases=clases)

    @classmethod
    def desde_modulo(cls, filtro_clases: Optional[Iterable[str]] = None) -> "CatalogoService":
        """Carga e indexa el catálogo para apertura."""
        clases = filtro_clases if filtro_clases is not None else ("Activo", "Pasivo", "Capital", "Patrimonio")
        return cls(filtro_clases=clases)

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


__all__ = [
    "PATRONES_REGULARIZADORAS",
    "SINONIMOS",
    "CatalogoService",
    "CuentaCatalogo",
    "es_cuenta_regularizadora",
    "normalizar",
]
