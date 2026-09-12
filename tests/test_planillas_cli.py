"""Pruebas unitarias para la capa CLI interactiva de planillas."""
import io
import unittest
from decimal import Decimal
from unittest.mock import patch

import planillas
from planilla import DatosEmpleado, ResultadoPlanilla, iniciar_flujo_planillas
from planilla.cli import flujo_interactivo, menu_herramientas_csv


class TestPlanillasCLI(unittest.TestCase):

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["0"])
    def test_iniciar_flujo_planillas_salir_inmediato(self, mock_input, mock_stdout):
        """Verifica que la opción 0 finalice el bucle con mensaje de despedida."""
        iniciar_flujo_planillas()
        salida = mock_stdout.getvalue()
        self.assertIn("SISTEMA DE PLANILLAS Y PARTIDAS CONTABLES", salida)
        self.assertIn("¡Hasta pronto!", salida)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["99", "0"])
    def test_opcion_invalida(self, mock_input, mock_stdout):
        """Verifica que una opción inválida muestre advertencia y continúe."""
        iniciar_flujo_planillas()
        salida = mock_stdout.getvalue()
        self.assertIn("Opción no reconocida. Intente nuevamente.", salida)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["99"])
    def test_menu_csv_opcion_invalida(self, mock_input, mock_stdout):
        """Verifica que una opción inválida en herramientas CSV muestre alerta."""
        menu_herramientas_csv([])
        salida = mock_stdout.getvalue()
        self.assertIn("Opción no reconocida. Intente nuevamente.", salida)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["n"])
    @patch("planilla.cli.solicitar_datos_interactivo")
    def test_flujo_interactivo_un_empleado(self, mock_solicitar, mock_input, mock_stdout):
        """Verifica el flujo interactivo para registrar un empleado y salir."""
        mock_solicitar.return_value = DatosEmpleado(
            nombre="Juan Perez",
            departamento="Administración",
            sueldo_base=Decimal("5000.00"),
        )
        resultados = flujo_interactivo()
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0].empleado, "Juan Perez")
        salida = mock_stdout.getvalue()
        self.assertIn("BOLETA DE PAGO: JUAN PEREZ", salida)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["4"])
    def test_menu_csv_volver(self, mock_input, mock_stdout):
        """Verifica la opción de volver al menú principal desde herramientas CSV."""
        res = menu_herramientas_csv([])
        self.assertEqual(res, [])
        salida = mock_stdout.getvalue()
        self.assertIn("HERRAMIENTAS CSV (OPCIONALES)", salida)

    def test_compatibilidad_retroactiva_planillas_py(self):
        """Verifica que planillas.py conserve los alias y atributos esperados."""
        self.assertTrue(callable(planillas.main))
        self.assertTrue(callable(planillas.iniciar_flujo_planillas))
        self.assertTrue(callable(planillas.calcular_planilla))
        self.assertTrue(callable(planillas.solicitar_datos_empleado))
        self.assertTrue(callable(planillas.flujo_interactivo))
        self.assertTrue(callable(planillas.menu_herramientas_csv))
