"""Pruebas unitarias para la capa de CLI, prompts y asistentes de diario/."""
from datetime import date
from decimal import Decimal
import unittest
from unittest.mock import patch

from diario.asistentes import registrar_apertura_asistida
from diario.cli import iniciar_flujo_diario
from diario.engine import GestorLibroDiario
from diario.prompts import buscar_o_seleccionar_cuenta, pedir_fecha, pedir_monto


class TestDiarioPrompts(unittest.TestCase):
    """Pruebas para las funciones de entrada y validación de terminal."""

    @patch("builtins.input", return_value="15/05/2026")
    def test_pedir_fecha_valida(self, mock_input):
        resultado = pedir_fecha()
        self.assertEqual(resultado, date(2026, 5, 15))

    @patch("builtins.input", return_value="")
    def test_pedir_fecha_default_hoy(self, mock_input):
        resultado = pedir_fecha()
        self.assertEqual(resultado, date.today())

    @patch("builtins.input", return_value="fecha-invalida")
    def test_pedir_fecha_invalida_fallback_hoy(self, mock_input):
        resultado = pedir_fecha()
        self.assertEqual(resultado, date.today())

    @patch("builtins.input", return_value="Q 2,500.75")
    def test_pedir_monto_con_formato_quetzales(self, mock_input):
        resultado = pedir_monto("Monto: ")
        self.assertEqual(resultado, Decimal("2500.75"))

    @patch("builtins.input", side_effect=["-10", "abc", "500.00"])
    def test_pedir_monto_reintentos_hasta_valido(self, mock_input):
        resultado = pedir_monto("Monto: ")
        self.assertEqual(resultado, Decimal("500.00"))

    @patch("builtins.input", return_value="1101")
    def test_buscar_o_seleccionar_cuenta_codigo_directo(self, mock_input):
        cod, nom = buscar_o_seleccionar_cuenta("Cuenta")
        self.assertEqual(cod, "1101")
        self.assertEqual(nom, "Caja General")

    @patch("builtins.input", return_value="Bancos")
    def test_buscar_o_seleccionar_cuenta_coincidencia_directa(self, mock_input):
        cod, nom = buscar_o_seleccionar_cuenta("Cuenta")
        self.assertEqual(cod, "1102")
        self.assertEqual(nom, "Bancos (Moneda Nacional)")

    @patch("builtins.input", side_effect=["Caja", "1"])
    def test_buscar_o_seleccionar_cuenta_multiple_con_seleccion(self, mock_input):
        cod, nom = buscar_o_seleccionar_cuenta("Cuenta")
        self.assertTrue(cod.startswith("1101"))


class TestDiarioCliYAsistentes(unittest.TestCase):
    """Pruebas para el menú interactivo y los asistentes."""

    @patch("builtins.input", return_value="0")
    def test_iniciar_flujo_diario_salir(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        # Debe salir de forma limpia sin lanzar excepciones
        iniciar_flujo_diario(gestor)
        self.assertEqual(len(gestor.libro.partidas), 0)

    @patch("builtins.input", side_effect=["1", ""])
    def test_registrar_apertura_asistida_demo(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        partida = registrar_apertura_asistida(gestor)
        self.assertIsNotNone(partida)
        self.assertEqual(len(gestor.libro.partidas), 1)
        self.assertEqual(partida.numero, 1)
        self.assertTrue(partida.cuadra)


if __name__ == "__main__":
    unittest.main()
