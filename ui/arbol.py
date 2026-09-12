# -*- coding: utf-8 -*-
"""Componente especializado en renderizar el Catálogo Contable como un Tree jerárquico."""
from typing import Optional
from rich.tree import Tree

from catalogo_contable import catalogo_cuentas
from ui.consola import console
from ui.temas import COLOR_AVISO, COLOR_EXITO, COLOR_PRIMARIO, COLOR_SECUNDARIO


def generar_arbol_catalogo(filtro_clase: Optional[str] = None) -> Tree:
    """Genera un árbol jerárquico de cuentas contables compatible con Rich."""
    titulo = "Catálogo Contable NIIF/SAT (Guatemala)"
    if filtro_clase:
        titulo += f" - Filtro: {filtro_clase}"
    arbol = Tree(f"[{COLOR_PRIMARIO}]{titulo}[/{COLOR_PRIMARIO}]")

    for clase, subgrupos in catalogo_cuentas.items():
        if filtro_clase and filtro_clase.lower() not in clase.lower():
            continue
        rama_clase = arbol.add(f"[{COLOR_AVISO}]{clase.upper()}[/{COLOR_AVISO}]")
        for subgrupo, cuentas in subgrupos.items():
            rama_subgrupo = rama_clase.add(f"[{COLOR_SECUNDARIO}]{subgrupo}[/{COLOR_SECUNDARIO}]")
            for codigo, nombre in cuentas.items():
                rama_subgrupo.add(f"[{COLOR_EXITO}]{str(codigo):<8}[/{COLOR_EXITO}] │ {nombre}")
    return arbol


def mostrar_catalogo_arbol(filtro_clase: Optional[str] = None, console_obj=None) -> None:
    """Muestra el catálogo contable en consola utilizando Rich Tree."""
    c = console_obj or console
    arbol = generar_arbol_catalogo(filtro_clase=filtro_clase)
    c.print(arbol)
