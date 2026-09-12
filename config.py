# -*- coding: utf-8 -*-
"""Configuración centralizada y constantes globales del Sistema Contable Integral."""
from decimal import Decimal

# -----------------------------------------------------------------------------
# CONSTANTES DE ARCHIVO Y PERSISTENCIA
# -----------------------------------------------------------------------------
ARCHIVO_EJERCICIO_DEFAULT: str = "libro_diario.json"
ARCHIVO_APERTURA_DEFAULT: str = "apertura_contable.txt"
ARCHIVO_PLANILLA_DEFAULT: str = "reporte_planilla.csv"
ARCHIVO_MAYOR_TG_DEFAULT: str = "t_graficas_mayor.txt"
ARCHIVO_MAYOR_FORMAL_DEFAULT: str = "libro_mayor_formal.txt"

# -----------------------------------------------------------------------------
# PARÁMETROS DE NAVEGACIÓN Y CONSOLA
# -----------------------------------------------------------------------------
OPCION_SALIR: str = "0"
RESPUESTAS_AFIRMATIVAS: tuple = ("s", "si", "y", "yes", "")
MENSAJE_ALERTA_OPCION: str = "Opción no reconocida. Intente nuevamente."

# -----------------------------------------------------------------------------
# MONEDA Y FORMATO
# -----------------------------------------------------------------------------
SIMBOLO_MONEDA: str = "Q"
PRECISION_CENTAVOS: Decimal = Decimal("0.01")
CERO_MONETARIO: Decimal = Decimal("0.00")

# -----------------------------------------------------------------------------
# NORMAS TRIBUTARIAS Y LABORALES (GUATEMALA)
# -----------------------------------------------------------------------------
TASA_IVA: Decimal = Decimal("0.12")
TASA_IGSS_LABORAL: Decimal = Decimal("0.0483")
TASA_IGSS_PATRONAL: Decimal = Decimal("0.1267")
BONIFICACION_INCENTIVO: Decimal = Decimal("250.00")
