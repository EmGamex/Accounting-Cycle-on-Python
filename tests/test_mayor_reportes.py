"""Pruebas unitarias para el renderizado y exportación de T-Gráficas y Libro Mayor."""
from datetime import date
from decimal import Decimal
import os
import unittest

from mayor.models import CuentaMayor, LibroMayor, MovimientoMayor
from reportes.libro_mayor import (
    exportar_reporte_libro_mayor,
    generar_texto_libro_mayor_formal,
    generar_texto_mayor_cuenta,
)
from reportes.t_graficas import (
    exportar_reporte_t_graficas,
    generar_texto_t_grafica,
    generar_texto_todas_t_graficas,
)


class TestReportesMayor(unittest.TestCase):
    """Pruebas para los reportes visuales de T-Gráficas y Libro Mayor a 3 columnas."""

    def setUp(self):
        self.caja = CuentaMayor(codigo="1101", nombre="Caja General")
        self.caja.movimientos.append(
            MovimientoMayor(1, date(2026, 1, 1), "Apertura de operaciones", debe=Decimal("15000.00"))
        )
        self.caja.movimientos.append(
            MovimientoMayor(2, date(2026, 1, 3), "Compra suministros", haber=Decimal("3000.00"))
        )

        self.gastos = CuentaMayor(codigo="5201", nombre="Gastos de Administración")
        self.gastos.movimientos.append(
            MovimientoMayor(2, date(2026, 1, 3), "Compra suministros", debe=Decimal("3000.00"))
        )

        self.capital = CuentaMayor(codigo="3101", nombre="Capital Social")
        self.capital.movimientos.append(
            MovimientoMayor(1, date(2026, 1, 1), "Aportación inicial", haber=Decimal("15000.00"))
        )

        self.mayor = LibroMayor(
            cuentas={
                "1101": self.caja,
                "5201": self.gastos,
                "3101": self.capital,
            }
        )

    def test_generar_texto_t_grafica_individual(self):
        texto = generar_texto_t_grafica(self.caja)
        self.assertIn("[1101] Caja General", texto)
        self.assertIn("DEBE (Cargos)", texto)
        self.assertIn("HABER (Abonos)", texto)
        self.assertIn("Pda #1", texto)
        self.assertIn("Q 15,000.00", texto)
        self.assertIn("Pda #2", texto)
        self.assertIn("Q 3,000.00", texto)
        self.assertIn("SALDO DEUDOR: Q 12,000.00", texto)

    def test_generar_texto_todas_t_graficas(self):
        texto = generar_texto_todas_t_graficas(self.mayor, empresa="EMPRESA DE PRUEBA")
        self.assertIn("EMPRESA DE PRUEBA", texto)
        self.assertIn("LIBRO MAYOR - REPORTE DE T-GRÁFICAS", texto)
        self.assertIn("[1101] Caja General", texto)
        self.assertIn("[3101] Capital Social", texto)
        self.assertIn("CUADRE EXACTO", texto)

    def test_generar_texto_mayor_cuenta_3_columnas(self):
        texto = generar_texto_mayor_cuenta(self.caja, folio=1)
        self.assertIn("CUENTA: [1101] Caja General", texto)
        self.assertIn("FOLIO: 01", texto)
        self.assertIn("FECHA", texto)
        self.assertIn("CONCEPTO / GLOSA", texto)
        self.assertIn("01/01/2026", texto)
        self.assertIn("03/01/2026", texto)
        self.assertIn("SUMAS Y SALDO FINAL:", texto)

    def test_generar_texto_libro_mayor_formal(self):
        texto = generar_texto_libro_mayor_formal(self.mayor)
        self.assertIn("LIBRO MAYOR DE OPERACIONES (A 3 COLUMNAS)", texto)
        self.assertIn("FOLIO: 01", texto)
        self.assertIn("FOLIO: 02", texto)
        self.assertIn("RESUMEN GENERAL DEL LIBRO MAYOR", texto)

    def test_exportar_reportes_a_disco(self):
        ruta_tg = "test_t_graficas_export.txt"
        ruta_lm = "test_libro_mayor_export.txt"
        try:
            res_tg = exportar_reporte_t_graficas(self.mayor, ruta_archivo=ruta_tg)
            self.assertTrue(os.path.exists(res_tg))

            res_lm = exportar_reporte_libro_mayor(self.mayor, ruta_archivo=ruta_lm)
            self.assertTrue(os.path.exists(res_lm))
        finally:
            if os.path.exists(ruta_tg):
                os.remove(ruta_tg)
            if os.path.exists(ruta_lm):
                os.remove(ruta_lm)
