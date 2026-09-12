"""Pruebas unitarias para la capa de CLI, prompts y asistentes de diario/."""
from datetime import date
from decimal import Decimal
import unittest
from unittest.mock import patch

from diario.asistentes import (
    registrar_apertura_asistida,
    registrar_compra_asistida,
    registrar_nomina_asistida,
    registrar_operacion_simple_asistida,
    registrar_partida_libre_asistida,
    registrar_venta_asistida,
)
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

    @patch("builtins.input", side_effect=[
        "2",          # Subopción 2 (manual con flujo de apertura)
        "1101",       # Cuenta Caja
        "5000.00",    # Monto Caja
        "fin",        # Fin de ingreso de cuentas
        "s",          # Asignar diferencia a Capital
        "",           # Fecha default hoy
    ])
    def test_registrar_apertura_asistida_con_flujo_completo_apertura(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        partida = registrar_apertura_asistida(gestor)
        self.assertIsNotNone(partida)
        self.assertEqual(len(gestor.libro.partidas), 1)
        self.assertEqual(partida.numero, 1)
        self.assertTrue(partida.cuadra)
        # Debe tener Caja y Capital Cuadrados en 5000.00
        self.assertEqual(partida.total_debe, Decimal("5000.00"))
        self.assertEqual(partida.total_haber, Decimal("5000.00"))

    @patch("builtins.input", side_effect=["99", "0"])
    def test_iniciar_flujo_diario_opcion_invalida(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        iniciar_flujo_diario(gestor)
        self.assertEqual(len(gestor.libro.partidas), 0)

    @patch("builtins.input", side_effect=["1", ""])
    def test_registrar_nomina_asistida_demo(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        partida = registrar_nomina_asistida(gestor)
        self.assertIsNotNone(partida)
        self.assertTrue(partida.cuadra)
        self.assertEqual(len(gestor.libro.partidas), 1)

    @patch("builtins.input", side_effect=[
        "Compra de suministros",  # Glosa
        "FAC-999",               # Doc
        "1120.00",               # Total factura
        "5201",                  # Cuenta gasto
        "",                      # Fecha (hoy)
        "1",                     # Condición contado
        "B",                     # Banco
    ])
    def test_registrar_compra_asistida_contado_banco(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        partida = registrar_compra_asistida(gestor)
        self.assertIsNotNone(partida)
        self.assertTrue(partida.cuadra)
        self.assertEqual(partida.total_debe, Decimal("1120.00"))

    @patch("builtins.input", side_effect=[
        "Venta de mercaderías",   # Glosa
        "FEL-1234",              # Doc
        "2240.00",               # Total venta
        "",                      # Fecha (hoy)
        "3",                     # Mixto
        "50",                    # 50% transferencia
    ])
    def test_registrar_venta_asistida_mixto(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        partida = registrar_venta_asistida(gestor)
        self.assertIsNotNone(partida)
        self.assertTrue(partida.cuadra)
        self.assertEqual(partida.total_haber, Decimal("2240.00"))

    @patch("builtins.input", side_effect=[
        "1",         # Opción 1: Cobro cliente
        "1500.00",   # Monto
        "B",         # Medio Banco
        "REC-101",   # Doc
        "",          # Fecha hoy
    ])
    def test_registrar_operacion_simple_abono_cliente(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        partida = registrar_operacion_simple_asistida(gestor)
        self.assertIsNotNone(partida)
        self.assertTrue(partida.cuadra)
        self.assertEqual(partida.total_debe, Decimal("1500.00"))

    @patch("builtins.input", side_effect=[
        "3",         # Opción 3: Depósito banco
        "3000.00",   # Monto
        "DEP-555",   # Doc
        "",          # Fecha hoy
    ])
    def test_registrar_operacion_simple_deposito_banco(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        partida = registrar_operacion_simple_asistida(gestor)
        self.assertIsNotNone(partida)
        self.assertTrue(partida.cuadra)
        self.assertEqual(partida.total_debe, Decimal("3000.00"))

    @patch("builtins.input", side_effect=[
        "Ajuste contable",  # Glosa
        "",                 # Doc
        "",                 # Fecha hoy
        "D",                # Debe
        "1101",             # Caja
        "500.00",           # Monto Debe
        "H",                # Haber
        "1102",             # Bancos
        "500.00",           # Monto Haber
        "fin",              # Concluir
    ])
    def test_registrar_partida_libre_asistida_cuadrada(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        partida = registrar_partida_libre_asistida(gestor)
        self.assertIsNotNone(partida)
        self.assertTrue(partida.cuadra)
        self.assertEqual(partida.total_debe, Decimal("500.00"))

    @patch("builtins.input", side_effect=[
        "Ajuste descuadrado",  # Glosa
        "",                    # Doc
        "",                    # Fecha hoy
        "D",                   # Debe
        "1101",                # Caja
        "500.00",              # Monto Debe
        "H",                   # Haber
        "1102",                # Bancos
        "400.00",              # Monto Haber (descuadrado)
        "fin",                 # Concluir
    ])
    def test_registrar_partida_libre_asistida_descuadrada(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        partida = registrar_partida_libre_asistida(gestor)
        self.assertIsNone(partida)
        self.assertEqual(len(gestor.libro.partidas), 0)


if __name__ == "__main__":
    unittest.main()


