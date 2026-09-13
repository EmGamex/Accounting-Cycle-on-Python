# -*- coding: utf-8 -*-
"""Constantes de configuración globales del Sistema Contable."""
from decimal import Decimal

# Archivos por defecto
ARCHIVO_EJERCICIO_DEFAULT: str = "libro_diario.json"
ARCHIVO_APERTURA_DEFAULT: str = "apertura_contable.txt"
ARCHIVO_PLANILLA_DEFAULT: str = "reporte_planilla.csv"
ARCHIVO_PLANTILLA_CSV_DEFAULT: str = "plantilla_empleados.csv"
ARCHIVO_MAYOR_TG_DEFAULT: str = "t_graficas_mayor.txt"
ARCHIVO_MAYOR_FORMAL_DEFAULT: str = "libro_mayor_formal.txt"
ARCHIVO_BALANCE_4C_DEFAULT: str = "balance_4_columnas.txt"
ARCHIVO_BALANCE_GENERAL_DEFAULT: str = "balance_situacion_general.txt"

# Formato y símbolos
SIMBOLO_MONEDA: str = "Q"
FORMATO_FECHA: str = "%d/%m/%Y"
FORMATO_MONEDA: str = "Q {:,.2f}"

# Tolerancias y precisión
PRECISION_CENTAVOS: Decimal = Decimal("0.01")
CERO_MONETARIO: Decimal = Decimal("0.00")

# Impuestos y tasas laborales Guatemala
TASA_IVA: Decimal = Decimal("0.12")
TASA_IGSS_LABORAL: Decimal = Decimal("0.0483")
TASA_IGSS_PATRONAL: Decimal = Decimal("0.1267")
BONIFICACION_INCENTIVO: Decimal = Decimal("250.00")

# Provisiones de pasivo laboral mensual
PROVISION_AGUINALDO: Decimal = Decimal("0.0833")       # 1/12
PROVISION_BONO_14: Decimal = Decimal("0.0833")         # 1/12
PROVISION_VACACIONES: Decimal = Decimal("0.0417")      # 15 días / 360
PROVISION_INDEMNIZACION: Decimal = Decimal("0.0833")   # 1/12

# Opciones de menú y navegación
OPCION_SALIR: str = "0"
RESPUESTAS_AFIRMATIVAS: tuple = ("s", "si", "y", "yes", "")
MENSAJE_ALERTA_OPCION: str = "Opción no reconocida. Intente nuevamente."
