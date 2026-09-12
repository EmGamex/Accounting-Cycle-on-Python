"""Pruebas unitarias para el menú orquestador principal main.py."""
import io
import os
import unittest
from unittest.mock import patch

from main import menu_principal


class TestMainOrquestador(unittest.TestCase):
    def setUp(self):
        patcher = patch("main.ARCHIVO_EJERCICIO_DEFAULT", "test_no_existe_diario.json")
        self.mock_archivo = patcher.start()
        self.addCleanup(patcher.stop)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["0"])
    def test_salir_inmediato(self, mock_input, mock_stdout):
        """Verifica salida limpia de main.py con opción 0."""
        menu_principal()
        salida = mock_stdout.getvalue()
        self.assertIn("SISTEMA CONTABLE INTEGRAL", salida)
        self.assertIn("¡Gracias por utilizar el Sistema Contable Integral!", salida)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["99", "0"])
    def test_opcion_invalida(self, mock_input, mock_stdout):
        """Verifica advertencia de opción no reconocida."""
        menu_principal()
        salida = mock_stdout.getvalue()
        self.assertIn("Opción no reconocida. Intente nuevamente.", salida)

    @patch("main.iniciar_flujo_apertura", return_value=(None, None))
    @patch("builtins.input", side_effect=["1", "0"])
    def test_invocacion_apertura(self, mock_input, mock_apertura):
        """Verifica que la opción 1 invoque el módulo de apertura."""
        menu_principal()
        mock_apertura.assert_called_once()

    @patch("main.iniciar_flujo_planillas", return_value=([], None))
    @patch("builtins.input", side_effect=["2", "0"])
    def test_invocacion_planillas(self, mock_input, mock_planillas):
        """Verifica que la opción 2 invoque el módulo de planillas."""
        menu_principal()
        mock_planillas.assert_called_once()

    @patch("main.iniciar_flujo_diario")
    @patch("builtins.input", side_effect=["3", "0"])
    def test_invocacion_diario(self, mock_input, mock_diario):
        """Verifica que la opción 3 invoque el módulo de libro diario pasando el gestor."""
        menu_principal()
        mock_diario.assert_called_once()
        self.assertIn("gestor", mock_diario.call_args.kwargs)

    @patch("main.iniciar_flujo_diario", side_effect=KeyboardInterrupt)
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["3", "0"])
    def test_manejo_keyboard_interrupt_submodulo(self, mock_input, mock_stdout, mock_diario):
        """Verifica que KeyboardInterrupt en un submódulo retorne al menú principal sin cerrarlo abruptamente."""
        menu_principal()
        salida = mock_stdout.getvalue()
        self.assertIn("Retornando al menú principal", salida)

    @patch("main.iniciar_flujo_mayor")
    @patch("builtins.input", side_effect=["4", "0"])
    def test_invocacion_mayor(self, mock_input, mock_mayor):
        """Verifica que la opción 4 invoque el módulo de libro mayor pasando el gestor."""
        menu_principal()
        mock_mayor.assert_called_once()
        self.assertIn("gestor_diario", mock_mayor.call_args.kwargs)

    @patch("main.iniciar_flujo_balance")
    @patch("builtins.input", side_effect=["5", "0"])
    def test_invocacion_balance(self, mock_input, mock_balance):
        """Verifica que la opción 5 invoque el módulo de balances pasando el gestor."""
        menu_principal()
        mock_balance.assert_called_once()
        self.assertIn("gestor_diario", mock_balance.call_args.kwargs)

    @patch("main.menu_persistencia")
    @patch("builtins.input", side_effect=["6", "0"])
    def test_invocacion_persistencia(self, mock_input, mock_persistencia):
        """Verifica que la opción 6 invoque el submenú de persistencia."""
        menu_principal()
        mock_persistencia.assert_called_once()

    @patch("main.iniciar_flujo_apertura")
    @patch("builtins.input", side_effect=["1", "s", "0", "n"])
    def test_asentar_apertura_en_diario(self, mock_input, mock_apertura):
        """Verifica que la partida de apertura se registre en el Gestor tras confirmar."""
        from decimal import Decimal
        from apertura.models import PartidaApertura, LineaPartida
        from diario.engine import GestorLibroDiario

        partida_ap = PartidaApertura(
            numero=1,
            descripcion="Partida de Apertura",
            lineas=[
                LineaPartida(codigo="1101", nombre="Caja", debe=Decimal("1000.00"), haber=Decimal("0.00")),
                LineaPartida(codigo="3101", nombre="Capital", debe=Decimal("0.00"), haber=Decimal("1000.00")),
            ],
            total_debe=Decimal("1000.00"),
            total_haber=Decimal("1000.00"),
        )
        mock_apertura.return_value = (None, partida_ap)

        gestor = GestorLibroDiario()
        menu_principal(gestor=gestor)

        self.assertEqual(len(gestor.libro.partidas), 1)
        self.assertEqual(gestor.libro.partidas[0].glosa, "Partida de Apertura")
        self.assertEqual(gestor.totales(), (Decimal("1000.00"), Decimal("1000.00")))

    @patch("main.iniciar_flujo_planillas")
    @patch("builtins.input", side_effect=["2", "s", "0", "n"])
    def test_asentar_nomina_en_diario(self, mock_input, mock_planillas):
        """Verifica que la partida de nómina se registre en el Gestor tras confirmar."""
        from decimal import Decimal
        from planilla.models import PartidaContable
        from diario.engine import GestorLibroDiario

        partida_nom = PartidaContable(
            debe=[("5201-01  Sueldos Administración", Decimal("4000.00"))],
            haber=[("1102     Bancos", Decimal("4000.00"))],
            total_debe=Decimal("4000.00"),
            total_haber=Decimal("4000.00"),
        )
        mock_planillas.return_value = ([], partida_nom)

        gestor = GestorLibroDiario()
        menu_principal(gestor=gestor)

        self.assertEqual(len(gestor.libro.partidas), 1)
        self.assertEqual(gestor.libro.partidas[0].numero, 1)
        self.assertEqual(gestor.totales(), (Decimal("4000.00"), Decimal("4000.00")))

    @patch("builtins.input", side_effect=["1", "0"])
    def test_menu_persistencia_guardar(self, mock_input):
        """Verifica el guardado desde el submenú de persistencia."""
        import tempfile
        from main import menu_persistencia
        from diario.engine import GestorLibroDiario

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = os.path.join(tmp_dir, "test_guardar.json")
            with patch("main.ARCHIVO_EJERCICIO_DEFAULT", test_file):
                gestor = GestorLibroDiario()
                menu_persistencia(gestor)
                self.assertTrue(os.path.exists(test_file))

    @patch("main.menu_principal")
    def test_main_entrypoint(self, mock_menu):
        """Verifica que main() invoque menu_principal()."""
        from main import main
        main()
        mock_menu.assert_called_once()

    @patch("main.menu_principal", side_effect=KeyboardInterrupt)
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_keyboard_interrupt(self, mock_stdout, mock_menu):
        """Verifica que main() capture KeyboardInterrupt y salga limpiamente."""
        from main import main
        with self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Sesión finalizada por el usuario", mock_stdout.getvalue())

    def test_orquestador_pedir_confirmacion(self):
        """Verifica la función auxiliar pedir_confirmacion."""
        import orquestador
        with patch("builtins.input", side_effect=["s", "si", "y", "yes", "n", "no", ""]):
            self.assertTrue(orquestador.pedir_confirmacion("¿Confirmar?"))
            self.assertTrue(orquestador.pedir_confirmacion("¿Confirmar?"))
            self.assertTrue(orquestador.pedir_confirmacion("¿Confirmar?"))
            self.assertTrue(orquestador.pedir_confirmacion("¿Confirmar?"))
            self.assertFalse(orquestador.pedir_confirmacion("¿Confirmar?"))
            self.assertFalse(orquestador.pedir_confirmacion("¿Confirmar?"))
            self.assertTrue(orquestador.pedir_confirmacion("¿Confirmar?", default=True))



