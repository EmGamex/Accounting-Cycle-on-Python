"""Pruebas unitarias para el renderizado y exportación de reportes de balances."""
from datetime import date
from decimal import Decimal
import os
import unittest

from balance.engine import generar_balance_4_columnas, generar_balance_general
from diario.models import LibroDiario, PartidaDiario
from mayor.engine import mayorizar_libro_diario
from reportes.balance import (
    exportar_reporte_balance_cierre,
    generar_texto_balance_general_cierre,
)
from reportes.balance_comprobacion import (
    exportar_reporte_balance_4_columnas,
    generar_texto_balance_4_columnas,
)


class TestBalanceReportes(unittest.TestCase):
    """Pruebas para reportes de texto y exportación de balances."""

    def setUp(self):
        self.libro_diario = LibroDiario()
        pda = PartidaDiario(numero=1, fecha=date(2026, 1, 1), glosa="Apertura")
        pda.agregar_cargo("1101", "Caja General", Decimal("20000.00"))
        pda.agregar_abono("3101", "Capital Social", Decimal("20000.00"))
        self.libro_diario.partidas.append(pda)

        self.mayor = mayorizar_libro_diario(self.libro_diario)
        self.b4 = generar_balance_4_columnas(self.mayor, empresa="EMPRESA TEST, S.A.")
        self.bg = generar_balance_general(self.mayor, empresa="EMPRESA TEST, S.A.")

    def test_generar_texto_balance_4_columnas(self):
        texto = generar_texto_balance_4_columnas(self.b4)
        self.assertIn("EMPRESA TEST, S.A.", texto)
        self.assertIn("BALANCE DE COMPROBACIÓN Y SALDOS (4 COLUMNAS)", texto)
        self.assertIn("1101", texto)
        self.assertIn("Caja General", texto)
        self.assertIn("SUMAS IGUALES:", texto)
        self.assertIn("CUADRADO EXACTO", texto)

    def test_generar_texto_balance_general_cierre(self):
        texto = generar_texto_balance_general_cierre(self.bg)
        self.assertIn("EMPRESA TEST, S.A.", texto)
        self.assertIn("BALANCE DE SITUACIÓN GENERAL DE CIERRE", texto)
        self.assertIn("1. ACTIVO", texto)
        self.assertIn("3. CAPITAL / PATRIMONIO NETO", texto)
        self.assertIn("TOTAL ACTIVO:", texto)
        self.assertIn("TOTAL PASIVO Y PATRIMONIO:", texto)
        self.assertIn("CUADRADO EXACTO", texto)

    def test_exportar_reportes_balance_a_disco(self):
        ruta_b4 = "temp_test_b4_export.txt"
        ruta_bg = "temp_test_bg_export.txt"
        try:
            res_b4 = exportar_reporte_balance_4_columnas(self.b4, ruta_archivo=ruta_b4)
            self.assertTrue(os.path.exists(res_b4))

            res_bg = exportar_reporte_balance_cierre(self.bg, ruta_archivo=ruta_bg)
            self.assertTrue(os.path.exists(res_bg))
        finally:
            if os.path.exists(ruta_b4):
                os.remove(ruta_b4)
            if os.path.exists(ruta_bg):
                os.remove(ruta_bg)


if __name__ == "__main__":
    unittest.main()
