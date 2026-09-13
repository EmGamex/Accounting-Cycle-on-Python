"""Pruebas unitarias para la liquidación y regularización del IVA en el Libro Diario."""
from datetime import date
from decimal import Decimal
import unittest
from unittest.mock import patch

from catalogo_contable import Cuenta
from diario.asistentes import regularizar_iva_asistido
from diario.cli import iniciar_flujo_diario
from diario.engine import GestorLibroDiario
from diario.models import TipoOrigenPartida
from diario.operaciones import (
    TIPO_RESULTADO_CERO,
    TIPO_RESULTADO_FAVOR,
    TIPO_RESULTADO_PAGAR,
    calcular_regularizacion_iva,
    crear_partida_compra,
    crear_partida_regularizacion_iva,
    crear_partida_venta,
)


class TestRegularizacionIvaOperaciones(unittest.TestCase):
    """Pruebas para el cálculo y creación de la partida de regularización."""

    def test_calculo_debito_mayor_que_credito(self):
        # Débito (2105) = 240.00, Crédito (1107) = 120.00 -> Compensar 120.00, Por pagar 120.00
        compensar, remanente, tipo = calcular_regularizacion_iva(Decimal("120.00"), Decimal("240.00"))
        self.assertEqual(compensar, Decimal("120.00"))
        self.assertEqual(remanente, Decimal("120.00"))
        self.assertEqual(tipo, TIPO_RESULTADO_PAGAR)

    def test_calculo_credito_mayor_que_debito(self):
        # Crédito (1107) = 300.00, Débito (2105) = 100.00 -> Compensar 100.00, A favor 200.00
        compensar, remanente, tipo = calcular_regularizacion_iva(Decimal("300.00"), Decimal("100.00"))
        self.assertEqual(compensar, Decimal("100.00"))
        self.assertEqual(remanente, Decimal("200.00"))
        self.assertEqual(tipo, TIPO_RESULTADO_FAVOR)

    def test_calculo_saldos_iguales(self):
        compensar, remanente, tipo = calcular_regularizacion_iva(Decimal("150.00"), Decimal("150.00"))
        self.assertEqual(compensar, Decimal("150.00"))
        self.assertEqual(remanente, Decimal("0.00"))
        self.assertEqual(tipo, TIPO_RESULTADO_CERO)

    def test_crear_partida_regularizacion_iva_estructura(self):
        partida = crear_partida_regularizacion_iva(
            numero=5,
            fecha=date(2026, 9, 30),
            monto=Decimal("120.00"),
        )
        self.assertEqual(partida.numero, 5)
        self.assertEqual(partida.fecha, date(2026, 9, 30))
        self.assertEqual(partida.origen, TipoOrigenPartida.AJUSTE)
        self.assertTrue(partida.cuadra)
        self.assertEqual(partida.total_debe, Decimal("120.00"))
        self.assertEqual(partida.total_haber, Decimal("120.00"))

        # Verificar cuentas: Debe a IVA Débito (2105), Haber a Crédito Fiscal (1107)
        cargos = partida.cargos
        abonos = partida.abonos
        self.assertEqual(len(cargos), 1)
        self.assertEqual(len(abonos), 1)
        self.assertEqual(cargos[0].codigo, Cuenta.IVA_DEBITO.value)
        self.assertEqual(abonos[0].codigo, Cuenta.IVA_CREDITO.value)


class TestGestorLibroDiarioIva(unittest.TestCase):
    """Pruebas para el cálculo de saldos acumulados de IVA en GestorLibroDiario."""

    def setUp(self):
        self.gestor = GestorLibroDiario(estricto_cronologico=False)

    def test_libro_vacio_saldos_cero(self):
        credito, debito = self.gestor.obtener_saldos_iva()
        self.assertEqual(credito, Decimal("0.00"))
        self.assertEqual(debito, Decimal("0.00"))
        self.assertFalse(self.gestor.puede_regularizar_iva())

    def test_saldos_tras_compra_y_venta(self):
        # 1. Compra por Q 1,120.00 (Base Q 1,000.00 + IVA Crédito Q 120.00)
        p_compra = crear_partida_compra(
            numero=1,
            fecha=date(2026, 9, 5),
            glosa="Compra de suministros",
            total_factura=Decimal("1120.00"),
            codigo_gasto=Cuenta.GASTOS_ADMIN.value,
            nombre_gasto="Gastos de Administración",
            pct_efectivo=Decimal("1.00"),
        )
        self.gestor.registrar_partida(p_compra)

        credito, debito = self.gestor.obtener_saldos_iva()
        self.assertEqual(credito, Decimal("120.00"))
        self.assertEqual(debito, Decimal("0.00"))
        self.assertFalse(self.gestor.puede_regularizar_iva())

        # 2. Venta por Q 2,240.00 (Base Q 2,000.00 + IVA Débito Q 240.00)
        p_venta = crear_partida_venta(
            numero=2,
            fecha=date(2026, 9, 10),
            glosa="Venta de mercaderías",
            total_factura=Decimal("2240.00"),
            pct_efectivo=Decimal("1.00"),
        )
        self.gestor.registrar_partida(p_venta)

        credito, debito = self.gestor.obtener_saldos_iva()
        self.assertEqual(credito, Decimal("120.00"))
        self.assertEqual(debito, Decimal("240.00"))
        self.assertTrue(self.gestor.puede_regularizar_iva())

        # 3. Registrar regularización por Q 120.00
        p_reg = crear_partida_regularizacion_iva(
            numero=3,
            fecha=date(2026, 9, 30),
            monto=Decimal("120.00"),
        )
        self.gestor.registrar_partida(p_reg)

        # Post-regularización: Crédito Fiscal queda en 0, Débito en 120
        credito_post, debito_post = self.gestor.obtener_saldos_iva()
        self.assertEqual(credito_post, Decimal("0.00"))
        self.assertEqual(debito_post, Decimal("120.00"))
        self.assertFalse(self.gestor.puede_regularizar_iva())


class TestAsistenteFiscalIva(unittest.TestCase):
    """Pruebas para el asistente interactivo regularizar_iva_asistido."""

    def setUp(self):
        self.gestor = GestorLibroDiario(estricto_cronologico=False)

    def test_regularizar_sin_saldos_retorna_none(self):
        partida = regularizar_iva_asistido(self.gestor)
        self.assertIsNone(partida)

    def test_regularizar_con_solo_compra_retorna_none(self):
        p_compra = crear_partida_compra(
            numero=1,
            fecha=date(2026, 9, 5),
            glosa="Compra",
            total_factura=Decimal("1120.00"),
            codigo_gasto=Cuenta.GASTOS_ADMIN.value,
            nombre_gasto="Gastos de Administración",
            pct_efectivo=Decimal("1.00"),
        )
        self.gestor.registrar_partida(p_compra)
        partida = regularizar_iva_asistido(self.gestor)
        self.assertIsNone(partida)

    @patch("builtins.input", side_effect=["s", ""])
    def test_regularizar_confirmado_registra_partida(self, mock_input):
        # Preparar compra y venta
        self.gestor.registrar_partida(
            crear_partida_compra(
                numero=1,
                fecha=date(2026, 9, 5),
                glosa="Compra",
                total_factura=Decimal("1120.00"),
                codigo_gasto=Cuenta.GASTOS_ADMIN.value,
                nombre_gasto="Gastos",
                pct_efectivo=Decimal("1.00"),
            )
        )
        self.gestor.registrar_partida(
            crear_partida_venta(
                numero=2,
                fecha=date(2026, 9, 10),
                glosa="Venta",
                total_factura=Decimal("2240.00"),
                pct_efectivo=Decimal("1.00"),
            )
        )

        partida = regularizar_iva_asistido(self.gestor)
        self.assertIsNotNone(partida)
        self.assertEqual(partida.numero, 3)
        self.assertEqual(partida.total_debe, Decimal("120.00"))
        self.assertEqual(len(self.gestor.libro.partidas), 3)

    @patch("builtins.input", return_value="n")
    def test_regularizar_cancelado_por_usuario(self, mock_input):
        self.gestor.registrar_partida(
            crear_partida_compra(
                numero=1,
                fecha=date(2026, 9, 5),
                glosa="Compra",
                total_factura=Decimal("1120.00"),
                codigo_gasto=Cuenta.GASTOS_ADMIN.value,
                nombre_gasto="Gastos",
                pct_efectivo=Decimal("1.00"),
            )
        )
        self.gestor.registrar_partida(
            crear_partida_venta(
                numero=2,
                fecha=date(2026, 9, 10),
                glosa="Venta",
                total_factura=Decimal("2240.00"),
                pct_efectivo=Decimal("1.00"),
            )
        )

        partida = regularizar_iva_asistido(self.gestor)
        self.assertIsNone(partida)
        self.assertEqual(len(self.gestor.libro.partidas), 2)


class TestDiarioCliFinalizarConIva(unittest.TestCase):
    """Pruebas para el prompt de regularización al salir del Libro Diario."""

    @patch("builtins.input", side_effect=["0", "s", "s", ""])
    def test_salir_con_saldos_iva_acepta_regularizacion(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        gestor.registrar_partida(
            crear_partida_compra(
                numero=1,
                fecha=date(2026, 9, 5),
                glosa="Compra",
                total_factura=Decimal("1120.00"),
                codigo_gasto=Cuenta.GASTOS_ADMIN.value,
                nombre_gasto="Gastos",
                pct_efectivo=Decimal("1.00"),
            )
        )
        gestor.registrar_partida(
            crear_partida_venta(
                numero=2,
                fecha=date(2026, 9, 10),
                glosa="Venta",
                total_factura=Decimal("2240.00"),
                pct_efectivo=Decimal("1.00"),
            )
        )

        # Entrada 1: "0" para salir
        # Entrada 2: "s" acepta sugerencia al finalizar de regularizar IVA
        # Entrada 3: "s" confirmación dentro de regularizar_iva_asistido
        # Entrada 4: "" fecha por defecto
        iniciar_flujo_diario(gestor)

        self.assertEqual(len(gestor.libro.partidas), 3)
        self.assertEqual(gestor.libro.partidas[-1].origen, TipoOrigenPartida.AJUSTE)

    @patch("builtins.input", side_effect=["0", "n"])
    def test_salir_con_saldos_iva_rechaza_regularizacion(self, mock_input):
        gestor = GestorLibroDiario(estricto_cronologico=False)
        gestor.registrar_partida(
            crear_partida_compra(
                numero=1,
                fecha=date(2026, 9, 5),
                glosa="Compra",
                total_factura=Decimal("1120.00"),
                codigo_gasto=Cuenta.GASTOS_ADMIN.value,
                nombre_gasto="Gastos",
                pct_efectivo=Decimal("1.00"),
            )
        )
        gestor.registrar_partida(
            crear_partida_venta(
                numero=2,
                fecha=date(2026, 9, 10),
                glosa="Venta",
                total_factura=Decimal("2240.00"),
                pct_efectivo=Decimal("1.00"),
            )
        )

        # Entrada 1: "0" salir
        # Entrada 2: "n" rechazar sugerencia
        iniciar_flujo_diario(gestor)

        self.assertEqual(len(gestor.libro.partidas), 2)


if __name__ == "__main__":
    unittest.main()
