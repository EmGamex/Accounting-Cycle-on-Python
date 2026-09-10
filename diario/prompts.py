"""Módulo de captura y validación de entradas por teclado para el Libro Diario."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

import catalogo_contable
from diario.engine import GestorLibroDiario


def pedir_fecha(mensaje: str = "Fecha (DD/MM/AAAA) [Hoy]: ") -> date:
    """Solicita una fecha por consola con valor por defecto la fecha actual."""
    entrada = input(mensaje).strip()
    if not entrada:
        return date.today()
    try:
        return datetime.strptime(entrada, "%d/%m/%Y").date()
    except ValueError:
        print("  (!) Formato inválido. Se usará la fecha de hoy.")
        return date.today()


def pedir_monto(mensaje: str) -> Decimal:
    """Solicita un monto decimal positivo."""
    while True:
        entrada = input(mensaje).strip().replace("Q", "").replace(",", "")
        try:
            val = Decimal(entrada).quantize(Decimal("0.01"))
            if val <= Decimal("0.00"):
                print("  (!) El monto debe ser mayor a 0.00.")
                continue
            return val
        except (InvalidOperation, ValueError):
            print("  (!) Monto no válido. Ingrese un valor numérico (ej. 1500.50).")


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
            print("  (!) Debe ingresar un código o nombre de cuenta.")
            continue

        # Si el código existe exactamente
        if entrada in catalogo_codigos:
            nombre = catalogo_codigos[entrada]
            return entrada, nombre

        # Búsqueda por término
        coincidencias = catalogo_contable.buscar_cuenta(entrada)
        if not coincidencias:
            print(f"  (!) No se encontró ninguna cuenta para '{entrada}'. Intente nuevamente.")
            continue

        if len(coincidencias) == 1:
            _, _, cod, nom = coincidencias[0]
            print(f"      -> Seleccionada: [{cod}] {nom}")
            return cod, nom

        print(f"  Coincidencias encontradas ({len(coincidencias)}):")
        for idx, (_, _, cod, nom) in enumerate(coincidencias[:7], 1):
            print(f"    [{idx}] {cod:<9} {nom}")
        sel = input("  Elija el número de la cuenta o presione Enter para buscar otra vez: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(coincidencias[:7]):
            _, _, cod, nom = coincidencias[int(sel) - 1]
            return cod, nom
