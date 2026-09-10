"""Pruebas unitarias completas para el módulo diario/ y la estructura unificada de PartidaDiario."""
from datetime import date, timedelta
from decimal import Decimal
import unittest

from apertura import CatalogoService, MotorApertura
from diario import (
    CorrelativoError,
    CuentaInvalidaError,
    DescuadrePartidaError,
    FechaInvalidaError,
    GestorLibroDiario,
    LibroDiario,
    MovimientoLinea,
    PartidaDiario,
    TipoOrigenPartida,
    crear_partida_abono_cliente,
    crear_partida_abono_prestamo,
    crear_partida_abono_proveedor,
    crear_partida_compra,
    crear_partida_deposito_banco,
    crear_partida_retiro_banco,
    crear_partida_simple,
    crear_partida_venta,
    de_partida_apertura,
    de_partida_planilla,
    generar_texto_libro_diario,
    generar_texto_partida,
)
from planilla.calculos import calcular_boleta
from planilla.contabilidad import generar_partida_contable
from planilla.models import DatosEmpleado


class TestModelosDiario(unittest.TestCase):
    """Pruebas para MovimientoLinea, PartidaDiario y LibroDiario."""

    def test_movimiento_linea_valida_y_propiedades(self):
        cargo = MovimientoLinea(codigo="1101", nombre="Caja General", debe=Decimal("500.00"))
        self.assertTrue(cargo.es_cargo)
        self.assertFalse(cargo.es_abono)
        self.assertEqual(cargo.monto, Decimal("500.00"))

        abono = MovimientoLinea(codigo="1102", nombre="Bancos", haber=Decimal("500.00"))
        self.assertFalse(abono.es_cargo)
        self.assertTrue(abono.es_abono)
        self.assertEqual(abono.monto, Decimal("500.00"))

    def test_movimiento_linea_rechaza_negativos_y_doble_imputacion(self):
        with self.assertRaises(ValueError):
            MovimientoLinea(codigo="1101", nombre="Caja", debe=Decimal("-10.00"))

        with self.assertRaises(ValueError):
            MovimientoLinea(codigo="1101", nombre="Caja", haber=Decimal("-10.00"))

        with self.assertRaises(ValueError):
            MovimientoLinea(
                codigo="1101",
                nombre="Caja",
                debe=Decimal("100.00"),
                haber=Decimal("50.00"),
            )

    def test_partida_diario_cuadre_y_diferencia(self):
        partida = PartidaDiario(
            numero=1,
            fecha=date(2026, 1, 1),
            glosa="Asiento de prueba",
        )
        partida.agregar_cargo("1101", "Caja General", Decimal("1500.00"))
        partida.agregar_abono("1102", "Bancos", Decimal("1000.00"))

        self.assertFalse(partida.cuadra)
        self.assertEqual(partida.diferencia, Decimal("500.00"))

        partida.agregar_abono("2101", "Proveedores Locales", Decimal("500.00"))
        self.assertTrue(partida.cuadra)
        self.assertEqual(partida.diferencia, Decimal("0.00"))
        self.assertEqual(len(partida.cargos), 1)
        self.assertEqual(len(partida.abonos), 2)


class TestGestorLibroDiario(unittest.TestCase):
    """Pruebas para el motor de reglas y validaciones del GestorLibroDiario."""

    def setUp(self):
        self.gestor = GestorLibroDiario(estricto_cronologico=True)

    def test_registro_partida_valida(self):
        partida = PartidaDiario(numero=1, fecha=date(2026, 1, 1), glosa="Apertura")
        partida.agregar_cargo("1101", "Caja General", Decimal("1000.00"))
        partida.agregar_abono("3101", "Capital Social", Decimal("1000.00"))

        p_reg = self.gestor.registrar_partida(partida)
        self.assertEqual(p_reg.numero, 1)
        self.assertEqual(len(self.gestor.libro.partidas), 1)
        self.assertEqual(self.gestor.totales(), (Decimal("1000.00"), Decimal("1000.00")))

    def test_rechazo_partida_descuadrada(self):
        partida = PartidaDiario(numero=1, fecha=date(2026, 1, 1), glosa="Descuadrada")
        partida.agregar_cargo("1101", "Caja General", Decimal("1000.00"))
        partida.agregar_abono("3101", "Capital Social", Decimal("900.00"))

        with self.assertRaises(DescuadrePartidaError):
            self.gestor.registrar_partida(partida)

    def test_rechazo_partida_sin_lineas(self):
        partida = PartidaDiario(numero=1, fecha=date(2026, 1, 1), glosa="Vacía")
        with self.assertRaises(DescuadrePartidaError):
            self.gestor.registrar_partida(partida)

    def test_control_correlativo_estricto(self):
        p1 = PartidaDiario(numero=1, fecha=date(2026, 1, 1), glosa="Pda 1")
        p1.agregar_cargo("1101", "Caja General", Decimal("100.00"))
        p1.agregar_abono("3101", "Capital Social", Decimal("100.00"))
        self.gestor.registrar_partida(p1)

        p3 = PartidaDiario(numero=3, fecha=date(2026, 1, 2), glosa="Pda 3 fuera de secuencia")
        p3.agregar_cargo("1101", "Caja General", Decimal("200.00"))
        p3.agregar_abono("3101", "Capital Social", Decimal("200.00"))

        with self.assertRaises(CorrelativoError):
            self.gestor.registrar_partida(p3)

        # Con auto_correlativo debe asignarle el #2
        p_corregida = self.gestor.registrar_partida(p3, auto_correlativo=True)
        self.assertEqual(p_corregida.numero, 2)

    def test_control_cronologico_estricto(self):
        p1 = PartidaDiario(numero=1, fecha=date(2026, 1, 10), glosa="Pda 1")
        p1.agregar_cargo("1101", "Caja General", Decimal("100.00"))
        p1.agregar_abono("3101", "Capital Social", Decimal("100.00"))
        self.gestor.registrar_partida(p1)

        p2 = PartidaDiario(numero=2, fecha=date(2026, 1, 5), glosa="Pda 2 fecha pasada")
        p2.agregar_cargo("1101", "Caja General", Decimal("100.00"))
        p2.agregar_abono("3101", "Capital Social", Decimal("100.00"))

        with self.assertRaises(FechaInvalidaError):
            self.gestor.registrar_partida(p2)

    def test_validacion_catalogo_contable(self):
        partida = PartidaDiario(numero=1, fecha=date(2026, 1, 1), glosa="Cuenta inexistente")
        partida.agregar_cargo("9999", "Cuenta Fantasma", Decimal("100.00"))
        partida.agregar_abono("3101", "Capital Social", Decimal("100.00"))

        with self.assertRaises(CuentaInvalidaError):
            self.gestor.registrar_partida(partida, validar_catalogo=True)

        # Si se desactiva validar_catalogo, debe permitir registrarla
        p_ok = self.gestor.registrar_partida(partida, validar_catalogo=False)
        self.assertEqual(p_ok.numero, 1)


class TestConectoresAperturaYPlanilla(unittest.TestCase):
    """Pruebas para los adaptadores de apertura y planilla hacia PartidaDiario."""

    def setUp(self):
        self.gestor = GestorLibroDiario()

    def test_conector_apertura(self):
        catalogo = CatalogoService.desde_modulo()
        motor_ap = MotorApertura()

        caja = catalogo.buscar("1101")
        bancos = catalogo.buscar("1102")
        proveedores = catalogo.buscar("2101")
        capital = catalogo.buscar("3101")

        assert caja is not None
        assert bancos is not None
        assert proveedores is not None
        assert capital is not None

        motor_ap.agregar_o_acumular(caja, Decimal("5000.00"))
        motor_ap.agregar_o_acumular(bancos, Decimal("15000.00"))
        motor_ap.agregar_o_acumular(proveedores, Decimal("4000.00"))
        res = motor_ap.calcular_balance()
        motor_ap.asignar_diferencia_capital(capital, res.diferencia_capital)

        pda_apertura = motor_ap.generar_partida_apertura(numero=1)
        partida_diario = de_partida_apertura(pda_apertura, fecha=date(2026, 1, 1))

        self.assertEqual(partida_diario.numero, 1)
        self.assertEqual(partida_diario.origen, TipoOrigenPartida.APERTURA)
        self.assertTrue(partida_diario.cuadra)
        self.assertEqual(partida_diario.total_debe, Decimal("20000.00"))
        self.assertEqual(partida_diario.total_haber, Decimal("20000.00"))

        # Debe registrarse limpiamente en el gestor
        self.gestor.registrar_partida(partida_diario)
        self.assertEqual(len(self.gestor.libro.partidas), 1)

    def test_conector_planilla(self):
        emp1 = DatosEmpleado(
            nombre="Juan Pérez",
            sueldo_base=Decimal("6000.00"),
            departamento="Administración",
            horas_extras=Decimal("5.0"),
        )
        emp2 = DatosEmpleado(
            nombre="María López",
            sueldo_base=Decimal("4500.00"),
            departamento="Ventas",
            ventas=Decimal("20000.00"),
            pct_comision=Decimal("0.03"),
        )

        res1 = calcular_boleta(emp1)
        res2 = calcular_boleta(emp2)
        pda_contable = generar_partida_contable([res1, res2])

        partida_diario = de_partida_planilla(pda_contable, fecha=date(2026, 1, 31), numero=1)

        self.assertEqual(partida_diario.numero, 1)
        self.assertEqual(partida_diario.origen, TipoOrigenPartida.PLANILLA)
        self.assertTrue(partida_diario.cuadra)
        self.assertGreater(partida_diario.total_debe, Decimal("0.00"))

        # Debe registrarse limpiamente en el gestor
        self.gestor.registrar_partida(partida_diario)
        self.assertEqual(len(self.gestor.libro.partidas), 1)


class TestOperacionesComercialesYReportes(unittest.TestCase):
    """Pruebas para generadores de compra, venta, simples y renderizado de texto."""

    def setUp(self):
        self.gestor = GestorLibroDiario()

    def test_partida_compra_con_iva(self):
        # Compra por Q 1,120.00 -> Base = Q 1,000.00, IVA Crédito Fiscal = Q 120.00
        pda_compra = crear_partida_compra(
            numero=1,
            fecha=date(2026, 1, 15),
            glosa="Compra de papelería para oficinas",
            total_factura=Decimal("1120.00"),
            codigo_gasto="5201",
            nombre_gasto="Gastos de Administración (Papelería)",
            codigo_pago="1102",
            nombre_pago="Bancos (Moneda Nacional)",
            documento_soporte="FAC-8921",
        )
        self.assertTrue(pda_compra.cuadra)
        self.assertEqual(pda_compra.total_debe, Decimal("1120.00"))
        self.assertEqual(pda_compra.total_haber, Decimal("1120.00"))
        self.assertEqual(pda_compra.documento_soporte, "FAC-8921")

        self.gestor.registrar_partida(pda_compra)
        self.assertEqual(len(self.gestor.libro.partidas), 1)

    def test_partida_venta_mixta_caso_usuario(self):
        """Verifica la venta de Q19,600 con 60% bancos y 40% crédito (caso del usuario)."""
        pda = crear_partida_venta(
            numero=1,
            fecha=date(2026, 1, 9),
            glosa="Ventas Q19,600.00 FEL: Crédito 40%, 60% Contado con transferencia",
            total_factura=Decimal("19600.00"),
            pct_banco=Decimal("0.60"),
            pct_credito=Decimal("0.40"),
            documento_soporte="FEL",
        )
        self.assertTrue(pda.cuadra)
        self.assertEqual(pda.total_debe, Decimal("19600.00"))
        self.assertEqual(pda.total_haber, Decimal("19600.00"))
        self.assertEqual(len(pda.lineas), 4)

        # Verificar desglose de cuentas
        lineas_dict = {l.codigo: l.monto for l in pda.lineas}
        self.assertEqual(lineas_dict["1102"], Decimal("11760.00"))  # Bancos (60%)
        self.assertEqual(lineas_dict["1103"], Decimal("7840.00"))   # Clientes (40%)
        self.assertEqual(lineas_dict["4101"], Decimal("17500.00"))  # Ventas (Base)
        self.assertEqual(lineas_dict["2105"], Decimal("2100.00"))   # IVA Débito Fiscal

        self.gestor.registrar_partida(pda)
        self.assertEqual(len(self.gestor.libro.partidas), 1)

    def test_partida_venta_reconciliacion_centavos(self):
        """Verifica que divisiones porcentuales complejas reconcilien centavos huérfanos sin descuadre."""
        pda = crear_partida_venta(
            numero=1,
            fecha=date(2026, 1, 9),
            glosa="Venta dividida en porcentajes no exactos",
            total_factura=Decimal("1000.00"),
            pct_banco=Decimal("33.33"),    # En base 100
            pct_credito=Decimal("66.67"),  # En base 100
        )
        self.assertTrue(pda.cuadra)
        self.assertEqual(pda.total_debe, Decimal("1000.00"))
        self.assertEqual(pda.total_haber, Decimal("1000.00"))

    def test_partida_compra_mixta(self):
        """Verifica compra con anticipo bancario y saldo con proveedores."""
        pda = crear_partida_compra(
            numero=1,
            fecha=date(2026, 1, 12),
            glosa="Compra de mercaderías con 20% anticipo bancario y 80% crédito",
            total_factura=Decimal("10000.00"),
            codigo_gasto="5102",
            nombre_gasto="Compras de Materia Prima",
            pct_banco=Decimal("0.20"),
            pct_proveedores=Decimal("0.80"),
            documento_soporte="FAC-1102",
        )
        self.assertTrue(pda.cuadra)
        self.assertEqual(pda.total_debe, Decimal("10000.00"))
        self.assertEqual(pda.total_haber, Decimal("10000.00"))

        lineas_dict = {l.codigo: l.monto for l in pda.lineas}
        self.assertEqual(lineas_dict["1102"], Decimal("2000.00"))  # Bancos (20%)
        self.assertEqual(lineas_dict["2101"], Decimal("8000.00"))  # Proveedores (80%)
        self.assertEqual(lineas_dict["5102"], Decimal("8928.57"))  # Base compra
        self.assertEqual(lineas_dict["1107"], Decimal("1071.43"))  # IVA Crédito Fiscal

    def test_partida_simple(self):
        pda_simple = crear_partida_simple(
            numero=1,
            fecha=date(2026, 1, 5),
            glosa="Depósito de efectivo en cuenta bancaria",
            monto=Decimal("3500.00"),
            codigo_debe="1102",
            nombre_debe="Bancos (Moneda Nacional)",
            codigo_haber="1101",
            nombre_haber="Caja General",
        )
        self.assertTrue(pda_simple.cuadra)
        self.assertEqual(pda_simple.total_debe, Decimal("3500.00"))

        self.gestor.registrar_partida(pda_simple)

    def test_reportes_texto(self):
        pda = crear_partida_simple(
            numero=1,
            fecha=date(2026, 1, 5),
            glosa="Traslado de fondos",
            monto=Decimal("1250.75"),
            codigo_debe="1102",
            nombre_debe="Bancos (Moneda Nacional)",
            codigo_haber="1101",
            nombre_haber="Caja General",
        )
        texto_pda = generar_texto_partida(pda)
        self.assertIn("PARTIDA No. 1", texto_pda)
        self.assertIn("SUMAS IGUALES:", texto_pda)
        self.assertIn("a: Caja General", texto_pda)
        self.assertIn("Q 1,250.75", texto_pda)

        self.gestor.registrar_partida(pda)
        texto_libro = generar_texto_libro_diario(self.gestor.libro)
        self.assertIn("LIBRO DIARIO DE OPERACIONES", texto_libro)
        self.assertIn("RESUMEN GENERAL DEL LIBRO DIARIO", texto_libro)
        self.assertIn("CUADRE EXACTO", texto_libro)

    def test_operaciones_frecuentes_helpers(self):
        """Verifica los generadores de alto nivel para cobros, pagos, depósitos y préstamos."""
        # 1. Abono de cliente en efectivo (Caso 11: Q 7,000)
        p1 = crear_partida_abono_cliente(
            numero=1,
            fecha=date(2026, 1, 15),
            monto=Decimal("7000.00"),
            medio="caja",
        )
        self.assertTrue(p1.cuadra)
        self.assertEqual(p1.lineas[0].codigo, "1101")  # Caja General
        self.assertEqual(p1.lineas[1].codigo, "1103")  # Clientes
        self.assertEqual(p1.total_debe, Decimal("7000.00"))
        self.gestor.registrar_partida(p1)

        # 2. Abono a proveedor con cheque (Caso 9: Q 8,000)
        p2 = crear_partida_abono_proveedor(
            numero=2,
            fecha=date(2026, 1, 16),
            monto=Decimal("8000.00"),
            medio="banco",
            documento_soporte="Ch.",
        )
        self.assertTrue(p2.cuadra)
        self.assertEqual(p2.lineas[0].codigo, "2101")  # Proveedores
        self.assertEqual(p2.lineas[1].codigo, "1102")  # Bancos
        self.assertEqual(p2.total_debe, Decimal("8000.00"))
        self.gestor.registrar_partida(p2)

        # 3. Abono a préstamo bancario (Caso 10: Q 12,000)
        p3 = crear_partida_abono_prestamo(
            numero=3,
            fecha=date(2026, 1, 17),
            monto=Decimal("12000.00"),
            documento_soporte="TRF-901",
        )
        self.assertTrue(p3.cuadra)
        self.assertEqual(p3.lineas[0].codigo, "2202")  # Préstamos Bancarios
        self.assertEqual(p3.lineas[1].codigo, "1102")  # Bancos
        self.assertEqual(p3.total_debe, Decimal("12000.00"))
        self.gestor.registrar_partida(p3)

        # 4. Depósito bancario de efectivo
        p4 = crear_partida_deposito_banco(
            numero=4,
            fecha=date(2026, 1, 18),
            monto=Decimal("5000.00"),
        )
        self.assertTrue(p4.cuadra)
        self.assertEqual(p4.lineas[0].codigo, "1102")  # Bancos
        self.assertEqual(p4.lineas[1].codigo, "1101")  # Caja
        self.gestor.registrar_partida(p4)

        # 5. Retiro de banco a caja
        p5 = crear_partida_retiro_banco(
            numero=5,
            fecha=date(2026, 1, 19),
            monto=Decimal("2000.00"),
        )
        self.assertTrue(p5.cuadra)
        self.assertEqual(p5.lineas[0].codigo, "1101")  # Caja
        self.assertEqual(p5.lineas[1].codigo, "1102")  # Bancos
        self.gestor.registrar_partida(p5)

        self.assertEqual(len(self.gestor.libro.partidas), 5)
        self.assertTrue(self.gestor.libro.cuadra)


if __name__ == "__main__":
    unittest.main()
