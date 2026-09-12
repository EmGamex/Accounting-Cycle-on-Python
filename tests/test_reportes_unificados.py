"""Pruebas unitarias para el paquete unificado de reportes contables."""
from datetime import date
from decimal import Decimal
import os
import unittest

from apertura import CatalogoService, MotorApertura
from diario.engine import GestorLibroDiario
from diario.operaciones.tesoreria import crear_partida_simple
from reportes import (
    centrar_titulo,
    exportar_archivo_texto,
    formato_moneda,
    generar_texto_balance,
    generar_texto_libro_diario,
    generar_texto_partida,
    linea_doble,
    linea_simple,
)


class TestReportesUnificados(unittest.TestCase):
    def test_formato_moneda(self):
        self.assertEqual(formato_moneda(Decimal("0.00")), "Q 0.00")
        self.assertEqual(formato_moneda(Decimal("1234.56")), "Q 1,234.56")
        self.assertEqual(formato_moneda(Decimal("1000000.00")), "Q 1,000,000.00")
        # Con ancho
        con_ancho = formato_moneda(Decimal("500.00"), ancho=12)
        self.assertEqual(len(con_ancho), 12)
        self.assertTrue(con_ancho.endswith("Q 500.00"))

    def test_lineas_y_titulos(self):
        self.assertEqual(linea_simple(10), "----------")
        self.assertEqual(linea_doble(10), "==========")
        titulo = centrar_titulo("HOLA", 10)
        self.assertEqual(len(titulo), 10)
        self.assertIn("HOLA", titulo)

    def test_generar_texto_partida_diario(self):
        pda = crear_partida_simple(
            numero=1,
            fecha=date(2026, 1, 10),
            glosa="Apertura de cuenta monetaria",
            monto=Decimal("5000.00"),
            codigo_debe="1102",
            nombre_debe="Bancos",
            codigo_haber="1101",
            nombre_haber="Caja General",
        )
        salida = generar_texto_partida(pda, ancho=80)
        self.assertIn("PARTIDA No. 1", salida)
        self.assertIn("10/01/2026", salida)
        self.assertIn("Bancos", salida)
        self.assertIn("a: Caja General", salida)
        self.assertIn("SUMAS IGUALES:", salida)
        self.assertIn("Q 5,000.00", salida)

    def test_generar_texto_partida_apertura(self):
        motor = MotorApertura()
        cat = CatalogoService.desde_modulo()
        motor.agregar_o_acumular(cat.buscar("1101"), Decimal("10000.00"))
        motor.agregar_o_acumular(cat.obtener_cuenta_capital(), Decimal("10000.00"))
        pda_apertura = motor.generar_partida_apertura(numero=1)

        salida = generar_texto_partida(pda_apertura, ancho=75, titulo_personalizado="PARTIDA DE DIARIO NO. 1 (ASIENTO DE APERTURA)")
        self.assertIn("PARTIDA DE DIARIO NO. 1 (ASIENTO DE APERTURA)", salida)
        self.assertIn("Caja General", salida)
        self.assertIn("a: Capital Social", salida)
        self.assertIn("SUMAS IGUALES:", salida)

    def test_generar_texto_libro_diario(self):
        gestor = GestorLibroDiario()
        pda = crear_partida_simple(
            numero=1,
            fecha=date(2026, 1, 1),
            glosa="Asiento 1",
            monto=Decimal("100.00"),
            codigo_debe="1101",
            nombre_debe="Caja",
            codigo_haber="1102",
            nombre_haber="Bancos",
        )
        gestor.registrar_partida(pda)
        texto = generar_texto_libro_diario(gestor.libro, empresa="TEST S.A.")
        self.assertIn("TEST S.A.", texto)
        self.assertIn("LIBRO DIARIO DE OPERACIONES", texto)
        self.assertIn("RESUMEN GENERAL DEL LIBRO DIARIO", texto)
        self.assertIn("Total de Partidas Registradas: 1", texto)
        self.assertIn("CUADRE EXACTO", texto)

    def test_generar_texto_balance_y_exportacion(self):
        motor = MotorApertura()
        cat = CatalogoService.desde_modulo()
        motor.agregar_o_acumular(cat.buscar("1101"), Decimal("25000.00"))
        motor.agregar_o_acumular(cat.obtener_cuenta_capital(), Decimal("25000.00"))
        resumen = motor.calcular_balance()

        texto_bal = generar_texto_balance(resumen)
        self.assertIn("BALANCE DE SITUACIÓN GENERAL DE APERTURA", texto_bal)
        self.assertIn("TOTAL ACTIVO:", texto_bal)
        self.assertIn("TOTAL PASIVO Y PATRIMONIO:", texto_bal)
        self.assertIn("CUADRADO EXACTO", texto_bal)

        ruta_test = "temp_test_reporte_unificado.txt"
        try:
            ruta_exportada = exportar_archivo_texto(texto_bal, ruta_test)
            self.assertTrue(os.path.exists(ruta_exportada))
            with open(ruta_exportada, "r", encoding="utf-8") as f:
                self.assertIn("BALANCE DE SITUACIÓN GENERAL DE APERTURA", f.read())
        finally:
            if os.path.exists(ruta_test):
                os.remove(ruta_test)


if __name__ == "__main__":
    unittest.main()
