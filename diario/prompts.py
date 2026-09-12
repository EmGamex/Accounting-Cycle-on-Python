"""Módulo de captura y validación de entradas por teclado para el Libro Diario."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

import catalogo_contable
from diario.engine import GestorLibroDiario

# Constantes de formato y presentación
FORMATO_FECHA = "%d/%m/%Y"
PRECISION_MONEDA = Decimal("0.01")
MONTO_MINIMO = Decimal("0.00")
MAX_COINCIDENCIAS = 7
PREFIJO_ALERTA = "  (!) "


def _mostrar_alerta(mensaje: str) -> None:
    """Imprime un mensaje formateado de advertencia o error en consola."""
    print(f"{PREFIJO_ALERTA}{mensaje}")


def _extraer_codigo_y_nombre(cuenta: tuple) -> tuple[str, str]:
    """Extrae únicamente el código y nombre de una tupla de catálogo."""
    return cuenta[2], cuenta[3]


def pedir_fecha(mensaje: str = "Fecha (DD/MM/AAAA) [Hoy]: ") -> date:
    """Solicita una fecha por consola con valor por defecto la fecha actual."""
    hoy = date.today()
    entrada = input(mensaje).strip()
    if not entrada:
        return hoy

    try:
        return datetime.strptime(entrada, FORMATO_FECHA).date()
    except ValueError:
        _mostrar_alerta("Formato inválido. Se usará la fecha de hoy.")
        return hoy


def pedir_monto(mensaje: str) -> Decimal:
    """Solicita un monto decimal positivo."""
    while True:
        entrada = input(mensaje).strip().upper().replace("Q", "").replace(",", "")
        try:
            val = Decimal(entrada).quantize(PRECISION_MONEDA)
            if val <= MONTO_MINIMO:
                _mostrar_alerta(f"El monto debe ser mayor a {MONTO_MINIMO}.")
                continue
            return val
        except (InvalidOperation, ValueError):
            _mostrar_alerta("Monto no válido. Ingrese un valor numérico (ej. 1500.50).")


def buscar_o_seleccionar_cuenta(
    mensaje: str,
    default_codigo: Optional[str] = None,
    gestor: Optional[GestorLibroDiario] = None,
) -> tuple[str, str]:
    """Permite ingresar un código contable o buscarlo interactivamente por nombre."""
    prompt = f"{mensaje} [{default_codigo}]: " if default_codigo else f"{mensaje}: "
    catalogo_codigos = (
        gestor._catalogo_codigos
        if gestor
        else {codigo.strip(): nombre.strip() for _, _, codigo, nombre in catalogo_contable.listar_cuentas()}
    )

    while True:
        entrada = input(prompt).strip()
        if not entrada and default_codigo:
            entrada = default_codigo

        if not entrada:
            _mostrar_alerta("Debe ingresar un código o nombre de cuenta.")
            continue

        # Coincidencia exacta por código
        if entrada in catalogo_codigos:
            return entrada, catalogo_codigos[entrada]

        # Búsqueda por término
        coincidencias = catalogo_contable.buscar_cuenta(entrada)
        if not coincidencias:
            _mostrar_alerta(f"No se encontró ninguna cuenta para '{entrada}'. Intente nuevamente.")
            continue

        # Si solo hay una coincidencia, se selecciona automáticamente
        if len(coincidencias) == 1:
            cod, nom = _extraer_codigo_y_nombre(coincidencias[0])
            print(f"      -> Seleccionada: [{cod}] {nom}")
            return cod, nom

        # Múltiples coincidencias: mostrar hasta el límite definido
        opciones = coincidencias[:MAX_COINCIDENCIAS]
        print(f"  Coincidencias encontradas ({len(coincidencias)}):")
        for idx, cuenta in enumerate(opciones, 1):
            cod, nom = _extraer_codigo_y_nombre(cuenta)
            print(f"    [{idx}] {cod:<9} {nom}")

        sel = input("  Elija el número de la cuenta o presione Enter para buscar otra vez: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(opciones):
            return _extraer_codigo_y_nombre(opciones[int(sel) - 1])
