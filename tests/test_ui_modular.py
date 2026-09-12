# -*- coding: utf-8 -*-
"""Pruebas unitarias para el paquete modular ui/."""
import io
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from apertura.models import LineaPartida, PartidaApertura
from diario.models import LibroDiario, PartidaDiario
from mayor.engine import GestorLibroMayor
from planilla.models import DatosEmpleado, ResultadoPlanilla, PartidaContable
import ui


class TestUIModular(unittest.TestCase):
    """Verifica que los componentes del paquete ui/ construyan y rendericen correctamente."""

    def test_exportaciones_principales(self):
        self.assertIsNotNone(ui.console)
        self.assertTrue(callable(ui.imprimir_banner))
        self.assertTrue(callable(ui.generar_tabla_partida))
        self.assertTrue(callable(ui.generar_arbol_catalogo))
        self.assertTrue(callable(ui.obtener_ancho_consola))

    def test_formatear_moneda(self):
        self.assertEqual(ui.formatear_moneda(Decimal("1250.50")), "Q1,250.50")
        self.assertEqual(ui.formatear_moneda(Decimal("0.00")), "Q0.00")

    def test_generar_tabla_partida(self):
        pda = PartidaApertura(
            numero=1,
            descripcion="Apertura Test",
            lineas=[
                LineaPartida(codigo="1101", nombre="Caja", debe=Decimal("100.00"), haber=Decimal("0.00")),
                LineaPartida(codigo="3101", nombre="Capital", debe=Decimal("0.00"), haber=Decimal("100.00")),
            ],
            total_debe=Decimal("100.00"),
            total_haber=Decimal("100.00"),
        )
        tabla = ui.generar_tabla_partida(pda)
        self.assertEqual(tabla.title, "Partida No. 1")
        self.assertEqual(len(tabla.columns), 4)

    def test_generar_tabla_sumas_y_saldos(self):
        diario = LibroDiario()
        pda = PartidaDiario(numero=1, fecha=date(2026, 1, 1), glosa="Apertura")
        pda.agregar_cargo("1101", "Caja", Decimal("500.00"))
        pda.agregar_abono("3101", "Capital", Decimal("500.00"))
        diario.partidas.append(pda)

        gestor_mayor = GestorLibroMayor(diario)
        mayor = gestor_mayor.sincronizar()
        tabla = ui.generar_tabla_sumas_y_saldos(mayor)
        self.assertIn("SUMAS Y SALDOS", tabla.title)
        self.assertEqual(len(tabla.columns), 6)

    def test_generar_arbol_catalogo(self):
        arbol = ui.generar_arbol_catalogo(filtro_clase="Activo")
        self.assertEqual(len(arbol.children), 1)

    def test_generar_tabla_cuentas_registradas(self):
        from apertura.models import ItemCuentaApertura
        ctas = [
            ItemCuentaApertura(codigo="1101", nombre="Caja", clase="Activo", subgrupo="Corriente", monto=Decimal("100.00"))
        ]
        tabla = ui.generar_tabla_cuentas_registradas(ctas)
        self.assertEqual(len(tabla.columns), 4)

    def test_generar_tabla_boleta_y_partida_nomina(self):
        res = ResultadoPlanilla(
            empleado="Carlos Gomez",
            departamento="Administración",
            sueldo_base=Decimal("3500.00"),
            comisiones=Decimal("0.00"),
            horas_extras_trabajadas=Decimal("0.00"),
            sueldo_extraordinario=Decimal("0.00"),
            bonificacion_ley=Decimal("250.00"),
            total_afecto_igss=Decimal("3500.00"),
            total_devengado=Decimal("3750.00"),
            descuento_igss=Decimal("169.05"),
            descuento_isr=Decimal("0.00"),
            prestamos_deudas=Decimal("0.00"),
            otros_descuentos=Decimal("0.00"),
            total_descuentos=Decimal("169.05"),
            liquido_recibir=Decimal("3580.95"),
        )
        tabla_boleta = ui.generar_tabla_boleta(res)
        self.assertIn("CARLOS GOMEZ", tabla_boleta.title)

        p = PartidaContable(
            debe=[("5201-01 Sueldos", Decimal("3500.00"))],
            haber=[("1102 Bancos", Decimal("3500.00"))],
            total_debe=Decimal("3500.00"),
            total_haber=Decimal("3500.00"),
        )
        tabla_pda = ui.generar_tabla_partida_nomina(p)
        self.assertIn("PARTIDA CONTABLE", tabla_pda.title)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_imprimir_banners_y_alertas(self, mock_stdout):
        ui.imprimir_banner("TITULO TEST")
        ui.imprimir_exito("Todo bien")
        ui.imprimir_alerta("Advertencia")
        ui.imprimir_aviso("Informacion")
        salida = mock_stdout.getvalue()
        self.assertIn("TITULO TEST", salida)
        self.assertIn("[OK]", salida)
        self.assertIn("(!)", salida)
        self.assertIn("[!]", salida)


if __name__ == "__main__":
    unittest.main()
