# -*- coding: utf-8 -*-
"""Pruebas unitarias para el módulo central de configuración config.py."""
import unittest
from decimal import Decimal
import config


class TestConfig(unittest.TestCase):
    """Verifica que las constantes globales y parámetros fiscales estén correctamente definidos."""

    def test_constantes_persistencia(self):
        self.assertTrue(config.ARCHIVO_EJERCICIO_DEFAULT.endswith(".json"))
        self.assertTrue(config.ARCHIVO_APERTURA_DEFAULT.endswith(".txt"))
        self.assertTrue(config.ARCHIVO_PLANILLA_DEFAULT.endswith(".csv"))
        self.assertTrue(config.ARCHIVO_PLANTILLA_CSV_DEFAULT.endswith(".csv"))

    def test_constantes_interaccion(self):
        self.assertEqual(config.OPCION_SALIR, "0")
        self.assertIn("s", config.RESPUESTAS_AFIRMATIVAS)
        self.assertIn("", config.RESPUESTAS_AFIRMATIVAS)
        self.assertIn("Opción no reconocida", config.MENSAJE_ALERTA_OPCION)

    def test_parametros_tributarios_guatemala(self):
        self.assertEqual(config.SIMBOLO_MONEDA, "Q")
        self.assertEqual(config.FORMATO_FECHA, "%d/%m/%Y")
        self.assertEqual(config.TASA_IVA, Decimal("0.12"))
        self.assertEqual(config.TASA_IGSS_LABORAL, Decimal("0.0483"))
        self.assertEqual(config.TASA_IGSS_PATRONAL, Decimal("0.1267"))
        self.assertEqual(config.BONIFICACION_INCENTIVO, Decimal("250.00"))
        self.assertEqual(config.PROVISION_AGUINALDO, Decimal("0.0833"))
        self.assertEqual(config.PROVISION_BONO_14, Decimal("0.0833"))
        self.assertEqual(config.PROVISION_VACACIONES, Decimal("0.0417"))
        self.assertEqual(config.PROVISION_INDEMNIZACION, Decimal("0.0833"))


if __name__ == "__main__":
    unittest.main()
