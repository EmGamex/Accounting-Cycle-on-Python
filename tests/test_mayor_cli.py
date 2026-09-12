"""Pruebas unitarias para el menú interactivo CLI de mayor/."""
from datetime import date
from decimal import Decimal
import io
import os
import unittest
from unittest.mock import patch

from diario.models import LibroDiario, PartidaDiario
from mayor.cli import iniciar_flujo_mayor
from mayor.engine import GestorLibroMayor


class TestMayorCLI(unittest.TestCase):
    """Pruebas del CLI del Libro Mayor."""

    def setUp(self):
        self.diario = LibroDiario()
        pda = PartidaDiario(numero=1, fecha=date(2026, 1, 1), glosa="Apertura")
        pda.agregar_cargo("1101", "Caja General", Decimal("5000.00"))
        pda.agregar_abono("3101", "Capital Social", Decimal("5000.00"))
        self.diario.partidas.append(pda)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["0"])
    def test_salir_inmediato(self, mock_input, mock_stdout):
        iniciar_flujo_mayor(gestor_diario=None)
        salida = mock_stdout.getvalue()
        self.assertIn("SISTEMA DE LIBRO MAYOR Y T-GRÁFICAS", salida)
        self.assertIn("Retornando al menú principal...", salida)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["1", "0"])
    def test_ver_todas_t_graficas(self, mock_input, mock_stdout):
        gestor_mayor = GestorLibroMayor(self.diario)
        iniciar_flujo_mayor(gestor_mayor=gestor_mayor)
        salida = mock_stdout.getvalue()
        self.assertIn("LIBRO MAYOR - REPORTE DE T-GRÁFICAS", salida)
        self.assertIn("[1101] Caja General", salida)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["2", "1101", "0"])
    def test_consultar_t_grafica_cuenta_especifica(self, mock_input, mock_stdout):
        gestor_mayor = GestorLibroMayor(self.diario)
        iniciar_flujo_mayor(gestor_mayor=gestor_mayor)
        salida = mock_stdout.getvalue()
        self.assertIn("[1101] Caja General", salida)
        self.assertIn("DEBE (Cargos)", salida)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["3", "0"])
    def test_ver_mayor_formal(self, mock_input, mock_stdout):
        gestor_mayor = GestorLibroMayor(self.diario)
        iniciar_flujo_mayor(gestor_mayor=gestor_mayor)
        salida = mock_stdout.getvalue()
        self.assertIn("LIBRO MAYOR DE OPERACIONES (A 3 COLUMNAS)", salida)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["4", "0"])
    def test_ver_resumen_sumas_y_saldos(self, mock_input, mock_stdout):
        gestor_mayor = GestorLibroMayor(self.diario)
        iniciar_flujo_mayor(gestor_mayor=gestor_mayor)
        salida = mock_stdout.getvalue()
        self.assertIn("RESUMEN DE CUENTAS MAYORIZADAS", salida)
        self.assertIn("1101", salida)

    @patch("builtins.input", side_effect=["5", "test_cli_tg.txt", "0"])
    def test_exportar_t_graficas(self, mock_input):
        gestor_mayor = GestorLibroMayor(self.diario)
        try:
            iniciar_flujo_mayor(gestor_mayor=gestor_mayor)
            self.assertTrue(os.path.exists("test_cli_tg.txt"))
        finally:
            if os.path.exists("test_cli_tg.txt"):
                os.remove("test_cli_tg.txt")
