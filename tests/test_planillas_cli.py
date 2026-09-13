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
    @patch("planilla.cli.cargar_empleados_csv")
    @patch("builtins.input", side_effect=["2"])
    def test_menu_csv_cargar_default(self, mock_input, mock_cargar, mock_stdout):
        """Verifica que la opción 2 cargue desde el archivo CSV default directamente."""
        mock_cargar.return_value = [
            DatosEmpleado(nombre="Ana Lopez", departamento="Ventas", sueldo_base=Decimal("6000.00"))
        ]
        res = menu_herramientas_csv([])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].empleado, "Ana Lopez")
        mock_cargar.assert_called_once_with("plantilla_empleados.csv")

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("planilla.cli.cargar_empleados_csv")
    @patch("builtins.input", side_effect=["3", "mi_ruta.csv"])
    def test_menu_csv_cargar_personalizado(self, mock_input, mock_cargar, mock_stdout):
        """Verifica que la opción 3 pida ruta y cargue desde la ruta especificada."""
        mock_cargar.return_value = [
            DatosEmpleado(nombre="Carlos Ruiz", departamento="Administración", sueldo_base=Decimal("4500.00"))
        ]
        res = menu_herramientas_csv([])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].empleado, "Carlos Ruiz")
        mock_cargar.assert_called_once_with("mi_ruta.csv")

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

    @patch("builtins.input", side_effect=["3", "1", "0"])
    def test_iniciar_flujo_planillas_ver_boletas(self, mock_input):
        """Verifica que se puedan ver las boletas de las planillas almacenadas."""
        from planilla.models import ResultadoPlanilla
        p1 = ResultadoPlanilla(
            empleado="Juan Perez",
            departamento="Administración",
            sueldo_base=Decimal("5000.00"),
            comisiones=Decimal("0.00"),
            horas_extras_trabajadas=Decimal("0.00"),
            sueldo_extraordinario=Decimal("0.00"),
            bonificacion_ley=Decimal("250.00"),
            total_afecto_igss=Decimal("5000.00"),
            total_devengado=Decimal("5250.00"),
            descuento_igss=Decimal("241.50"),
            descuento_isr=Decimal("0.00"),
            prestamos_deudas=Decimal("0.00"),
            otros_descuentos=Decimal("0.00"),
            total_descuentos=Decimal("241.50"),
            liquido_recibir=Decimal("5008.50"),
        )
        planillas_res, partida = iniciar_flujo_planillas(planillas_iniciales=[p1])
        self.assertEqual(len(planillas_res), 1)
        self.assertIsNotNone(partida)

    @patch("builtins.input", side_effect=["4", "1", "2", "0"])
    def test_iniciar_flujo_planillas_eliminar_empleado(self, mock_input):
        """Verifica que se pueda eliminar un empleado de la lista almacenada."""
        from planilla.models import ResultadoPlanilla
        p1 = ResultadoPlanilla(
            empleado="Juan Perez",
            departamento="Administración",
            sueldo_base=Decimal("5000.00"),
            comisiones=Decimal("0.00"),
            horas_extras_trabajadas=Decimal("0.00"),
            sueldo_extraordinario=Decimal("0.00"),
            bonificacion_ley=Decimal("250.00"),
            total_afecto_igss=Decimal("5000.00"),
            total_devengado=Decimal("5250.00"),
            descuento_igss=Decimal("241.50"),
            descuento_isr=Decimal("0.00"),
            prestamos_deudas=Decimal("0.00"),
            otros_descuentos=Decimal("0.00"),
            total_descuentos=Decimal("241.50"),
            liquido_recibir=Decimal("5008.50"),
        )
        planillas_res, partida = iniciar_flujo_planillas(planillas_iniciales=[p1])
        self.assertEqual(len(planillas_res), 0)


if __name__ == "__main__":
    unittest.main()
