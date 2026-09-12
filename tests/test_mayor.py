"""Pruebas unitarias para el módulo mayor/ (Modelos y Motor de Mayorización)."""
from datetime import date
from decimal import Decimal
import unittest

from diario.models import LibroDiario, MovimientoLinea, PartidaDiario
from mayor.engine import GestorLibroMayor, mayorizar_libro_diario
from mayor.exceptions import DescuadreMayorError, LibroDiarioVacioError
from mayor.models import CuentaMayor, LibroMayor, MovimientoMayor, NaturalezaSaldo


class TestMayorModels(unittest.TestCase):
    """Pruebas de modelos y comportamiento contable de cuentas en el Mayor."""

    def test_movimiento_mayor_propiedades_y_validaciones(self):
        mov_cargo = MovimientoMayor(
            numero_partida=1,
            fecha=date(2026, 1, 1),
            concepto="Apertura",
            debe=Decimal("1500.00"),
        )
        self.assertTrue(mov_cargo.es_cargo)
        self.assertFalse(mov_cargo.es_abono)
        self.assertEqual(mov_cargo.monto, Decimal("1500.00"))

        mov_abono = MovimientoMayor(
            numero_partida=2,
            fecha=date(2026, 1, 2),
            concepto="Pago",
            haber=Decimal("500.00"),
        )
        self.assertFalse(mov_abono.es_cargo)
        self.assertTrue(mov_abono.es_abono)
        self.assertEqual(mov_abono.monto, Decimal("500.00"))

    def test_movimiento_mayor_rechaza_valores_invalidos(self):
        with self.assertRaises(ValueError):
            MovimientoMayor(
                numero_partida=1,
                fecha=date(2026, 1, 1),
                concepto="Test",
                debe=Decimal("-10.00"),
            )

        with self.assertRaises(ValueError):
            MovimientoMayor(
                numero_partida=1,
                fecha=date(2026, 1, 1),
                concepto="Test",
                debe=Decimal("10.00"),
                haber=Decimal("20.00"),
            )

    def test_cuenta_mayor_calculo_saldo_deudor(self):
        cuenta = CuentaMayor(codigo="1101", nombre="Caja General")
        cuenta.movimientos.append(
            MovimientoMayor(1, date(2026, 1, 1), "Apertura", debe=Decimal("1000.00"))
        )
        cuenta.movimientos.append(
            MovimientoMayor(2, date(2026, 1, 2), "Cobro", debe=Decimal("500.00"))
        )
        cuenta.movimientos.append(
            MovimientoMayor(3, date(2026, 1, 3), "Pago", haber=Decimal("300.00"))
        )

        self.assertEqual(cuenta.total_debe, Decimal("1500.00"))
        self.assertEqual(cuenta.total_haber, Decimal("300.00"))
        self.assertEqual(cuenta.saldo, Decimal("1200.00"))
        self.assertEqual(cuenta.tipo_saldo, NaturalezaSaldo.DEUDOR)
        self.assertEqual(cuenta.saldo_deudor, Decimal("1200.00"))
        self.assertEqual(cuenta.saldo_acreedor, Decimal("0.00"))
        self.assertFalse(cuenta.es_saldo_anomalo)

    def test_cuenta_mayor_calculo_saldo_acreedor(self):
        cuenta = CuentaMayor(codigo="2101", nombre="Proveedores Locales")
        cuenta.movimientos.append(
            MovimientoMayor(1, date(2026, 1, 1), "Factura compra", haber=Decimal("5000.00"))
        )
        cuenta.movimientos.append(
            MovimientoMayor(2, date(2026, 1, 2), "Abono deuda", debe=Decimal("2000.00"))
        )

        self.assertEqual(cuenta.total_debe, Decimal("2000.00"))
        self.assertEqual(cuenta.total_haber, Decimal("5000.00"))
        self.assertEqual(cuenta.saldo, Decimal("3000.00"))
        self.assertEqual(cuenta.tipo_saldo, NaturalezaSaldo.ACREEDOR)
        self.assertEqual(cuenta.saldo_deudor, Decimal("0.00"))
        self.assertEqual(cuenta.saldo_acreedor, Decimal("3000.00"))
        self.assertFalse(cuenta.es_saldo_anomalo)

    def test_cuenta_mayor_saldada(self):
        cuenta = CuentaMayor(codigo="1103", nombre="Clientes")
        cuenta.movimientos.append(
            MovimientoMayor(1, date(2026, 1, 1), "Venta al crédito", debe=Decimal("1000.00"))
        )
        cuenta.movimientos.append(
            MovimientoMayor(2, date(2026, 1, 5), "Cobro total", haber=Decimal("1000.00"))
        )

        self.assertEqual(cuenta.saldo, Decimal("0.00"))
        self.assertEqual(cuenta.tipo_saldo, NaturalezaSaldo.SALDADA)
        self.assertEqual(cuenta.saldo_deudor, Decimal("0.00"))
        self.assertEqual(cuenta.saldo_acreedor, Decimal("0.00"))
        self.assertFalse(cuenta.es_saldo_anomalo)

    def test_cuenta_mayor_detecta_saldo_anomalo(self):
        cuenta = CuentaMayor(codigo="1101", nombre="Caja General")
        cuenta.movimientos.append(
            MovimientoMayor(1, date(2026, 1, 1), "Salida en exceso", haber=Decimal("100.00"))
        )
        self.assertEqual(cuenta.tipo_saldo, NaturalezaSaldo.ACREEDOR)
        self.assertTrue(cuenta.es_saldo_anomalo)

    def test_libro_mayor_cuadre_y_totales(self):
        caja = CuentaMayor(codigo="1101", nombre="Caja General")
        caja.movimientos.append(MovimientoMayor(1, date(2026, 1, 1), "Apertura", debe=Decimal("1000.00")))

        capital = CuentaMayor(codigo="3101", nombre="Capital Social")
        capital.movimientos.append(MovimientoMayor(1, date(2026, 1, 1), "Apertura", haber=Decimal("1000.00")))

        mayor = LibroMayor(cuentas={"1101": caja, "3101": capital})
        self.assertEqual(mayor.total_debe, Decimal("1000.00"))
        self.assertEqual(mayor.total_haber, Decimal("1000.00"))
        self.assertEqual(mayor.total_saldos_deudores, Decimal("1000.00"))
        self.assertEqual(mayor.total_saldos_acreedores, Decimal("1000.00"))
        self.assertTrue(mayor.cuadra)
        self.assertEqual(mayor.diferencia_sumas, Decimal("0.00"))
        self.assertEqual(mayor.diferencia_saldos, Decimal("0.00"))


class TestMotorMayorizacion(unittest.TestCase):
    """Pruebas de pase del Libro Diario al Libro Mayor."""

    def setUp(self):
        self.libro_diario = LibroDiario()

        pda1 = PartidaDiario(numero=1, fecha=date(2026, 1, 1), glosa="Apertura")
        pda1.agregar_cargo("1101", "Caja General", Decimal("10000.00"))
        pda1.agregar_cargo("1102", "Bancos", Decimal("15000.00"))
        pda1.agregar_abono("3101", "Capital Social", Decimal("25000.00"))
        self.libro_diario.partidas.append(pda1)

        pda2 = PartidaDiario(numero=2, fecha=date(2026, 1, 2), glosa="Compra mercaderías")
        pda2.agregar_cargo("5102", "Compras de Materia Prima", Decimal("5000.00"))
        pda2.agregar_cargo("1107", "Crédito Fiscal", Decimal("600.00"))
        pda2.agregar_abono("1102", "Bancos", Decimal("5600.00"))
        self.libro_diario.partidas.append(pda2)

    def test_mayorizar_libro_diario_exitoso(self):
        mayor = mayorizar_libro_diario(self.libro_diario)
        self.assertTrue(mayor.cuadra)
        self.assertEqual(mayor.total_debe, self.libro_diario.total_debe)
        self.assertEqual(mayor.total_haber, self.libro_diario.total_haber)
        self.assertEqual(len(mayor.cuentas), 5)

        bancos = mayor.obtener_cuenta("1102")
        self.assertIsNotNone(bancos)
        self.assertEqual(bancos.total_debe, Decimal("15000.00"))
        self.assertEqual(bancos.total_haber, Decimal("5600.00"))
        self.assertEqual(bancos.saldo, Decimal("9400.00"))
        self.assertEqual(bancos.tipo_saldo, NaturalezaSaldo.DEUDOR)
        self.assertEqual(len(bancos.movimientos), 2)
        self.assertEqual(bancos.movimientos[0].numero_partida, 1)
        self.assertEqual(bancos.movimientos[1].numero_partida, 2)

    def test_mayorizar_libro_vacio_lanza_error_por_defecto(self):
        vacio = LibroDiario()
        with self.assertRaises(LibroDiarioVacioError):
            mayorizar_libro_diario(vacio)

    def test_mayorizar_libro_vacio_permitido(self):
        vacio = LibroDiario()
        mayor = mayorizar_libro_diario(vacio, permitir_vacio=True)
        self.assertEqual(len(mayor.cuentas), 0)

    def test_mayorizar_libro_descuadrado_lanza_descuadre_error(self):
        diario_malo = LibroDiario()
        pda = PartidaDiario(numero=1, fecha=date(2026, 1, 1), glosa="Descuadrada")
        pda.lineas.append(MovimientoLinea("1101", "Caja", debe=Decimal("100.00")))
        pda.lineas.append(MovimientoLinea("3101", "Capital", haber=Decimal("90.00")))
        diario_malo.partidas.append(pda)

        with self.assertRaises(DescuadreMayorError):
            mayorizar_libro_diario(diario_malo, validar_cuadre_diario=True)

    def test_gestor_libro_mayor_sincronizacion(self):
        gestor = GestorLibroMayor(self.libro_diario)
        mayor = gestor.libro_mayor
        self.assertEqual(len(mayor.cuentas), 5)

        pda3 = PartidaDiario(numero=3, fecha=date(2026, 1, 3), glosa="Abono")
        pda3.agregar_cargo("1101", "Caja General", Decimal("1000.00"))
        pda3.agregar_abono("1102", "Bancos", Decimal("1000.00"))
        self.libro_diario.partidas.append(pda3)

        mayor_actualizado = gestor.sincronizar()
        caja = mayor_actualizado.obtener_cuenta("1101")
        self.assertEqual(caja.total_debe, Decimal("11000.00"))
