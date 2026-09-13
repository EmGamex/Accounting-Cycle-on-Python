"""Pruebas unitarias para validar el catálogo, el motor contable y el cuadre de aperturas."""
from decimal import Decimal
import os
import unittest
from unittest.mock import patch

from apertura import (
    CatalogoService,
    MotorApertura,
    es_cuenta_regularizadora,
    exportar_reporte,
    generar_texto_balance,
    generar_texto_partida,
    normalizar,
)
from apertura.models import CuentaCatalogo


class TestAperturaContable(unittest.TestCase):

    def setUp(self):
        self.catalogo = CatalogoService.desde_modulo()
        self.motor = MotorApertura()

    def test_normalizar_y_regularizadoras(self):
        """Verifica la normalización de texto y la detección de cuentas regularizadoras."""
        self.assertEqual(normalizar("  (-) Depreciación Acumulada  "), "depreciacion acumulada")
        self.assertTrue(es_cuenta_regularizadora("(-) Depreciación Acumulada"))
        self.assertTrue(es_cuenta_regularizadora("Estimación para Cuentas Incobrables"))
        self.assertTrue(es_cuenta_regularizadora("Pérdidas Acumuladas"))
        self.assertFalse(es_cuenta_regularizadora("Caja General"))
        self.assertFalse(es_cuenta_regularizadora("Proveedores Locales"))

    def test_busqueda_catalogo_codigo_y_nombre(self):
        """Verifica búsquedas exactas O(1) por código y por nombre con sinónimos."""
        # Por código
        cta = self.catalogo.buscar("1101")
        self.assertIsNotNone(cta)
        self.assertEqual(cta.nombre, "Caja General")

        # Por nombre exacto
        cta2 = self.catalogo.buscar("caja general")
        self.assertIsNotNone(cta2)
        self.assertEqual(cta2.codigo, "1101")

        # Por sinónimo
        cta_banco = self.catalogo.buscar("banco")
        self.assertIsNotNone(cta_banco)
        self.assertIn("Bancos", cta_banco.nombre)

        # Por similitud / token
        cta_vehiculo = self.catalogo.buscar("vehiculo")
        self.assertIsNotNone(cta_vehiculo)
        self.assertEqual(cta_vehiculo.nombre, "Vehículos")

    def test_buscar_coincidencias_multiples(self):
        """Verifica que buscar_coincidencias retorne todas las cuentas relevantes para selección interactiva."""
        coincidencias = self.catalogo.buscar_coincidencias("depreciacion")
        self.assertGreater(len(coincidencias), 1)
        # Verificar que incluya subcuentas específicas
        codigos = [c.codigo for c in coincidencias]
        self.assertIn("1205", codigos)
        self.assertIn("1205-01", codigos)

        # Búsqueda por código exacto debe retornar 1 sola
        exacta = self.catalogo.buscar_coincidencias("1101")
        self.assertEqual(len(exacta), 1)
        self.assertEqual(exacta[0].nombre, "Caja General")

    def test_acumulacion_y_eliminacion_de_cuentas(self):
        """Verifica que montos sobre la misma cuenta se acumulen y se puedan eliminar."""
        cta = self.catalogo.buscar("1101")  # Caja General
        self.motor.agregar_o_acumular(cta, Decimal("1000.00"))
        self.motor.agregar_o_acumular(cta, Decimal("500.50"))

        self.assertEqual(len(self.motor.items), 1)
        self.assertEqual(self.motor.items[0].monto, Decimal("1500.50"))

        eliminado = self.motor.eliminar("1101")
        self.assertTrue(eliminado)
        self.assertEqual(len(self.motor.items), 0)

    def test_cuadre_balance_con_cuentas_regularizadoras(self):
        """Verifica que las cuentas regularizadoras resten en el balance y cuadren exactamente."""
        # Activo: Vehículos (100,000) y Depreciación Acumulada (20,000) -> Activo Neto = 80,000
        cta_veh = self.catalogo.buscar("1206")  # Vehículos
        cta_dep = self.catalogo.buscar("1205")  # (-) Depreciación Acumulada
        self.motor.agregar_o_acumular(cta_veh, Decimal("100000.00"))
        self.motor.agregar_o_acumular(cta_dep, Decimal("20000.00"))

        # Pasivo: Préstamos Bancarios (30,000)
        cta_pasivo = self.catalogo.buscar("2202")  # Préstamos Bancarios a Largo Plazo
        self.motor.agregar_o_acumular(cta_pasivo, Decimal("30000.00"))

        resumen = self.motor.calcular_balance()

        # Activo neto esperado: 100,000 - 20,000 = 80,000
        self.assertEqual(resumen.total_activo, Decimal("80000.00"))
        # Pasivo: 30,000
        self.assertEqual(resumen.total_pasivo, Decimal("30000.00"))
        # Diferencia de capital necesaria: 80,000 - 30,000 = 50,000
        self.assertEqual(resumen.diferencia_capital, Decimal("50000.00"))
        self.assertFalse(resumen.cuadra)

        # Ajuste a capital
        cta_cap = self.catalogo.obtener_cuenta_capital()
        self.motor.asignar_diferencia_capital(cta_cap, resumen.diferencia_capital)

        resumen_cuadrado = self.motor.calcular_balance()
        self.assertTrue(resumen_cuadrado.cuadra)
        self.assertEqual(resumen_cuadrado.total_patrimonio, Decimal("50000.00"))
        self.assertEqual(resumen_cuadrado.total_activo, resumen_cuadrado.total_pasivo_y_patrimonio)

    def test_partida_apertura_sumas_iguales(self):
        """Verifica que la partida de diario de apertura cuadre con sumas iguales exactas (Debe == Haber)."""
        # Debe: Caja (10,000) + Bancos (40,000) + Vehículos (50,000) = 100,000
        self.motor.agregar_o_acumular(self.catalogo.buscar("1101"), Decimal("10000.00"))
        self.motor.agregar_o_acumular(self.catalogo.buscar("1102"), Decimal("40000.00"))
        self.motor.agregar_o_acumular(self.catalogo.buscar("1206"), Decimal("50000.00"))

        # Haber: Depreciación Acumulada (10,000) + Proveedores (20,000) + Capital Social (70,000) = 100,000
        self.motor.agregar_o_acumular(self.catalogo.buscar("1205"), Decimal("10000.00"))
        self.motor.agregar_o_acumular(self.catalogo.buscar("2101"), Decimal("20000.00"))
        self.motor.agregar_o_acumular(self.catalogo.obtener_cuenta_capital(), Decimal("70000.00"))

        partida = self.motor.generar_partida_apertura(numero=1)

        self.assertTrue(partida.cuadra)
        self.assertEqual(partida.total_debe, Decimal("100000.00"))
        self.assertEqual(partida.total_haber, Decimal("100000.00"))
        self.assertEqual(partida.diferencia, Decimal("0.00"))

        # Verificar que la regularizadora de activo (Depreciación Acumulada) se colocó en el Haber
        dep_linea = next(l for l in partida.lineas if "Depreciación" in l.nombre)
        self.assertEqual(dep_linea.haber, Decimal("10000.00"))
        self.assertEqual(dep_linea.debe, Decimal("0.00"))

    def test_exportar_reporte(self):
        """Verifica la exportación del reporte consolidado a archivo físico."""
        self.motor.agregar_o_acumular(self.catalogo.buscar("1101"), Decimal("5000.00"))
        self.motor.agregar_o_acumular(self.catalogo.obtener_cuenta_capital(), Decimal("5000.00"))

        resumen = self.motor.calcular_balance()
        partida = self.motor.generar_partida_apertura()

        ruta_test = "temp_test_apertura.txt"
        try:
            ruta_exportada = exportar_reporte(resumen, partida, ruta_test)
            self.assertTrue(os.path.exists(ruta_exportada))
            with open(ruta_exportada, "r", encoding="utf-8") as f:
                contenido = f.read()
                self.assertIn("BALANCE DE SITUACIÓN GENERAL DE APERTURA", contenido)
                self.assertIn("PARTIDA DE DIARIO NO. 1", contenido)
                self.assertIn("Caja General", contenido)
        finally:
            if os.path.exists(ruta_test):
                os.remove(ruta_test)

    @patch("builtins.input", side_effect=[
        "1101",
        "8000.00",
        "fin",
        "s",  # Cuadrar con capital
        "n",  # No exportar a txt
    ])
    def test_iniciar_flujo_apertura_retorno(self, mock_input):
        """Verifica que iniciar_flujo_apertura retorne correctamente resumen y partida."""
        from apertura.cli import iniciar_flujo_apertura
        resumen, partida = iniciar_flujo_apertura(numero_partida=3, exportar_archivo=True)
        self.assertIsNotNone(resumen)
        self.assertIsNotNone(partida)
        self.assertEqual(partida.numero, 3)
        self.assertTrue(partida.cuadra)
        self.assertEqual(partida.total_debe, Decimal("8000.00"))

    @patch("builtins.input", side_effect=["9", "invalido", "1"])
    def test_pedir_clasificacion_manual_reintentos(self, mock_input):
        """Verifica que pedir_clasificacion_manual reintente hasta obtener una opción válida (1-5)."""
        from apertura.cli import pedir_clasificacion_manual
        opcion = pedir_clasificacion_manual("Cuenta Desconocida")
        self.assertEqual(opcion, "1")

    def test_motor_apertura_items_iniciales_y_modificar(self):
        """Verifica que MotorApertura precargue cuentas y permita modificar montos directamente."""
        from apertura.models import ItemCuentaApertura
        item_inicial = ItemCuentaApertura(
            codigo="1101",
            nombre="Caja General",
            monto=Decimal("5000.00"),
            clase="1. Activo",
            subgrupo="1.1 Activo Corriente",
        )
        motor = MotorApertura(items_iniciales=[item_inicial])
        self.assertEqual(len(motor.items), 1)
        self.assertEqual(motor.items[0].monto, Decimal("5000.00"))

        # Modificar monto directamente
        actualizado = motor.modificar_monto("1101", Decimal("7500.00"))
        self.assertIsNotNone(actualizado)
        self.assertEqual(actualizado.monto, Decimal("7500.00"))
        self.assertEqual(motor.items[0].monto, Decimal("7500.00"))

    @patch("builtins.input", side_effect=[
        "modificar",
        "1101",
        "9000.00",
        "fin",
        "s",  # Cuadrar capital
        "n",  # No exportar txt
    ])
    def test_iniciar_flujo_apertura_con_cuentas_iniciales(self, mock_input):
        """Verifica que iniciar_flujo_apertura precargue las cuentas y permita modificarlas interactivamente."""
        from apertura.cli import iniciar_flujo_apertura
        from apertura.models import ItemCuentaApertura

        item_caja = ItemCuentaApertura(
            codigo="1101",
            nombre="Caja General",
            monto=Decimal("5000.00"),
            clase="1. Activo",
            subgrupo="1.1 Activo Corriente",
        )
        resumen, partida = iniciar_flujo_apertura(
            numero_partida=1,
            exportar_archivo=False,
            imprimir_reportes=False,
            cuentas_iniciales=[item_caja],
        )
        self.assertIsNotNone(partida)
        self.assertEqual(partida.total_debe, Decimal("9000.00"))


if __name__ == "__main__":
    unittest.main()

