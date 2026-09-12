"""Pruebas unitarias para el menú interactivo CLI de balances."""
import io
import unittest
from unittest.mock import MagicMock, patch

from balance.cli import iniciar_flujo_balance
from balance.engine import GestorBalance


class TestBalanceCLI(unittest.TestCase):
    """Pruebas de la capa interactiva CLI de Balances."""

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["0"])
    def test_salir_inmediato(self, mock_input, mock_stdout):
        iniciar_flujo_balance()
        salida = mock_stdout.getvalue()
        self.assertIn("SISTEMA DE BALANCES: 4 COLUMNAS Y SITUACIÓN GENERAL", salida)
        self.assertIn("Retornando al menú principal...", salida)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["1", "0"])
    def test_ver_balance_4_columnas(self, mock_input, mock_stdout):
        mock_gestor = MagicMock(spec=GestorBalance)
        mock_gestor.obtener_balance_4_columnas.return_value.filas = []
        mock_gestor.obtener_balance_4_columnas.return_value.cuadra = True
        mock_gestor.obtener_balance_4_columnas.return_value.total_debe = 0
        mock_gestor.obtener_balance_4_columnas.return_value.total_haber = 0
        mock_gestor.obtener_balance_4_columnas.return_value.total_saldos_deudores = 0
        mock_gestor.obtener_balance_4_columnas.return_value.total_saldos_acreedores = 0

        iniciar_flujo_balance(gestor_balance=mock_gestor)
        salida = mock_stdout.getvalue()
        self.assertIn("BALANCE DE COMPROBACIÓN Y SALDOS (4 COLUMNAS)", salida)


if __name__ == "__main__":
    unittest.main()
