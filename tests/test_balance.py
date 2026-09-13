"""Pruebas unitarias para el módulo balance/ (Modelos y Motor de 4 Columnas y Cierre)."""
from datetime import date
from decimal import Decimal
import unittest

from balance.engine import (
    GestorBalance,
    calcular_estado_resultados,
    generar_balance_4_columnas,
    generar_balance_general,
)
from balance.exceptions import (
    BalanceError,
    BalanceVacioError,
    DescuadreBalanceError,
    EcuacionPatrimonialError,
)
from balance.models import (
    Balance4Columnas,
    BalanceSituacionGeneral,
    FilaBalance4Columnas,
    ItemBalanceGeneral,
    ResumenResultados,
)
from diario.engine import GestorLibroDiario
from diario.models import LibroDiario, MovimientoLinea, PartidaDiario
from mayor.engine import mayorizar_libro_diario
from mayor.models import CuentaMayor, LibroMayor, MovimientoMayor


class TestBalanceModelsYEngine(unittest.TestCase):
    """Pruebas para los modelos y el motor analítico de balances."""

    def setUp(self):
        self.libro_diario = LibroDiario()

        # Partida 1: Apertura
        pda1 = PartidaDiario(numero=1, fecha=date(2026, 1, 1), glosa="Apertura")
        pda1.agregar_cargo("1101", "Caja General", Decimal("10000.00"))
        pda1.agregar_cargo("1102", "Bancos", Decimal("40000.00"))
        pda1.agregar_cargo("1204", "Mobiliario y Equipo", Decimal("15000.00"))
        pda1.agregar_abono("2101", "Proveedores Locales", Decimal("5000.00"))
        pda1.agregar_abono("3101", "Capital Social", Decimal("60000.00"))
        self.libro_diario.partidas.append(pda1)

        # Partida 2: Operación de Ventas
        pda2 = PartidaDiario(numero=2, fecha=date(2026, 1, 10), glosa="Venta al contado")
        pda2.agregar_cargo("1101", "Caja General", Decimal("11200.00"))
        pda2.agregar_abono("4101", "Ventas de Mercancías", Decimal("10000.00"))
        pda2.agregar_abono("2105", "IVA por Pagar", Decimal("1200.00"))
        self.libro_diario.partidas.append(pda2)

        # Partida 3: Gastos de Administración
        pda3 = PartidaDiario(numero=3, fecha=date(2026, 1, 15), glosa="Pago de alquileres y servicios")
        pda3.agregar_cargo("5201", "Gastos de Administración", Decimal("3000.00"))
        pda3.agregar_abono("1102", "Bancos", Decimal("3000.00"))
        self.libro_diario.partidas.append(pda3)

        self.mayor = mayorizar_libro_diario(self.libro_diario)

    def test_generar_balance_4_columnas_exitoso(self):
        b4 = generar_balance_4_columnas(self.mayor)
        self.assertTrue(b4.cuadran_sumas)
        self.assertTrue(b4.cuadran_saldos)
        self.assertTrue(b4.cuadra)
        self.assertEqual(b4.diferencia_sumas, Decimal("0.00"))
        self.assertEqual(b4.diferencia_saldos, Decimal("0.00"))
        self.assertEqual(len(b4.filas), 8)

        fila_caja = b4.obtener_fila("1101")
        self.assertIsNotNone(fila_caja)
        self.assertEqual(fila_caja.suma_debe, Decimal("21200.00"))
        self.assertEqual(fila_caja.suma_haber, Decimal("0.00"))
        self.assertEqual(fila_caja.saldo_deudor, Decimal("21200.00"))
        self.assertEqual(fila_caja.saldo_acreedor, Decimal("0.00"))

    def test_generar_balance_vacio_lanza_error_por_defecto(self):
        vacio = LibroMayor()
        with self.assertRaises(BalanceVacioError):
            generar_balance_4_columnas(vacio)

    def test_generar_balance_vacio_permitido(self):
        vacio = LibroMayor()
        b4 = generar_balance_4_columnas(vacio, permitir_vacio=True)
        self.assertEqual(len(b4.filas), 0)
        self.assertEqual(b4.total_debe, Decimal("0.00"))

    def test_calcular_estado_resultados(self):
        b4 = generar_balance_4_columnas(self.mayor)
        res = calcular_estado_resultados(b4)
        self.assertEqual(res.total_ingresos, Decimal("10000.00"))
        self.assertEqual(res.total_costos, Decimal("0.00"))
        self.assertEqual(res.total_gastos, Decimal("3000.00"))
        self.assertEqual(res.resultado_ejercicio, Decimal("7000.00"))
        self.assertTrue(res.es_ganancia)

    def test_generar_balance_general_cierre_cuadre(self):
        bg = generar_balance_general(self.mayor)
        self.assertTrue(bg.cuadra)
        self.assertEqual(bg.diferencia, Decimal("0.00"))

        # Total Activo: Caja (21,200) + Bancos (37,000) + Mobiliario (15,000) = 73,200
        self.assertEqual(bg.total_activo, Decimal("73200.00"))

        # Total Pasivo: Proveedores (5,000) + IVA por Pagar (1,200) = 6,200
        self.assertEqual(bg.total_pasivo, Decimal("6200.00"))

        # Total Patrimonio: Capital Social (60,000) + Resultado Ejercicio (7,000) = 67,000
        self.assertEqual(bg.total_patrimonio, Decimal("67000.00"))

        # Activo (73,200) == Pasivo + Patrimonio (6,200 + 67,000 = 73,200)
        self.assertEqual(bg.total_pasivo_y_patrimonio, Decimal("73200.00"))

    def test_balance_general_con_cuenta_regularizadora(self):
        # Agregar depreciación acumulada a mobiliario
        pda_deprec = PartidaDiario(numero=4, fecha=date(2026, 1, 31), glosa="Depreciación período")
        pda_deprec.agregar_cargo("5201", "Gastos de Administración", Decimal("1500.00"))
        pda_deprec.agregar_abono("1205-03", "(-) Deprec. Acum. Mobiliario", Decimal("1500.00"))
        self.libro_diario.partidas.append(pda_deprec)

        mayor_actualizado = mayorizar_libro_diario(self.libro_diario)
        bg = generar_balance_general(mayor_actualizado)
        self.assertTrue(bg.cuadra)
        self.assertEqual(bg.diferencia, Decimal("0.00"))

    def test_gestor_balance_sincronizacion(self):
        gestor_diario = GestorLibroDiario()
        for p in self.libro_diario.partidas:
            gestor_diario.registrar_partida(p, auto_correlativo=True)

        gestor_bal = GestorBalance(gestor_diario=gestor_diario)
        b4 = gestor_bal.obtener_balance_4_columnas(sincronizar=True)
        self.assertEqual(len(b4.filas), 8)

        bg = gestor_bal.obtener_balance_general(sincronizar=True)
        self.assertTrue(bg.cuadra)


if __name__ == "__main__":
    unittest.main()
