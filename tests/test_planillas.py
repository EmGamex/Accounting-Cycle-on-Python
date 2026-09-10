"""Pruebas unitarias para validar cálculos, precisión Decimal y cuadre contable."""
import os
import unittest
from decimal import Decimal

from planilla import (
    BONIFICACION_LEY,
    DatosEmpleado,
    ResultadoPlanilla,
    calcular_boleta,
    calcular_isr_mensual,
    cargar_empleados_csv,
    crear_plantilla_csv_ejemplo,
    exportar_planilla_csv,
    generar_partida_contable,
    money,
)


class TestPlanilla(unittest.TestCase):

    def test_precision_decimal_money(self):
        """Verifica que el helper de redondeo redondee a dos decimales sin error binario."""
        self.assertEqual(money(100.555), Decimal("100.56"))
        self.assertEqual(money("100.554"), Decimal("100.55"))
        self.assertEqual(money(Decimal("50.00")), Decimal("50.00"))

    def test_calculo_boleta_basico(self):
        """Verifica el cálculo de una boleta sin comisiones ni horas extras."""
        emp = DatosEmpleado(
            nombre="Carlos Ruiz",
            departamento="Administración",
            sueldo_base=Decimal("5000.00"),
        )
        res = calcular_boleta(emp)

        # IGSS: 5000 * 0.0483 = 241.50
        self.assertEqual(res.descuento_igss, Decimal("241.50"))
        # Devengado: 5000 + 250 = 5250.00
        self.assertEqual(res.total_devengado, Decimal("5250.00"))
        # ISR mensual proyectado (60,000 - 48,000 - 2,898) * 5% / 12 = 37.93
        self.assertEqual(res.descuento_isr, Decimal("37.93"))
        # Líquido: 5250 - 241.50 - 37.93 = 4970.57
        self.assertEqual(res.liquido_recibir, Decimal("4970.57"))

    def test_calculo_horas_extras_y_comisiones(self):
        """Verifica horas extras con jornada diurna (8h) y comisiones."""
        emp = DatosEmpleado(
            nombre="Laura Paz",
            departamento="Ventas",
            sueldo_base=Decimal("4800.00"),
            ventas=Decimal("20000.00"),
            pct_comision=Decimal("5.00"),  # 1,000.00
            horas_extras=Decimal("10.00"),
            jornada_horas=Decimal("8.0"),
        )
        # Valor hora: (4800 / 30 / 8) * 1.5 = 20 * 1.5 = 30.00
        # Extraordinario: 10 * 30.00 = 300.00
        res = calcular_boleta(emp)
        self.assertEqual(res.comisiones, Decimal("1000.00"))
        self.assertEqual(res.sueldo_extraordinario, Decimal("300.00"))

        # Afecto IGSS: 4800 + 1000 + 300 = 6100.00
        self.assertEqual(res.total_afecto_igss, Decimal("6100.00"))
        # IGSS: 6100 * 0.0483 = 294.63
        self.assertEqual(res.descuento_igss, Decimal("294.63"))

    def test_partida_contable_cuadre_exacto(self):
        """Verifica que la partida contable cuadre al centavo (Debe == Haber)."""
        empleados = [
            DatosEmpleado(
                nombre="Emp 1",
                departamento="Administración",
                sueldo_base=Decimal("4500.00"),
                horas_extras=Decimal("5.00"),
                prestamos_deudas=Decimal("150.00"),
            ),
            DatosEmpleado(
                nombre="Emp 2",
                departamento="Ventas",
                sueldo_base=Decimal("3800.00"),
                ventas=Decimal("35000.00"),
                pct_comision=Decimal("2.50"),
                otros_descuentos=Decimal("75.00"),
            ),
            DatosEmpleado(
                nombre="Emp 3",
                departamento="Administración",
                sueldo_base=Decimal("8500.00"),
                isr_manual=Decimal("180.50"),
            ),
        ]

        resultados = [calcular_boleta(e) for e in empleados]
        partida = generar_partida_contable(resultados, separar_departamentos=True)

        self.assertTrue(partida.cuadra)
        self.assertEqual(partida.diferencia, Decimal("0.00"))
        self.assertEqual(partida.total_debe, partida.total_haber)

    def test_funciones_csv_futuro(self):
        """Verifica que la exportación y carga CSV funcionen correctamente."""
        ruta_temp_plantilla = "temp_plantilla_test.csv"
        ruta_temp_export = "temp_export_test.csv"

        try:
            # 1. Crear plantilla
            crear_plantilla_csv_ejemplo(ruta_temp_plantilla)
            self.assertTrue(os.path.exists(ruta_temp_plantilla))

            # 2. Cargar plantilla creada
            cargados = cargar_empleados_csv(ruta_temp_plantilla)
            self.assertGreaterEqual(len(cargados), 2)
            self.assertEqual(cargados[0].nombre, "Juan Pérez")

            # 3. Calcular y exportar
            resultados = [calcular_boleta(e) for e in cargados]
            exportar_planilla_csv(resultados, ruta_temp_export)
            self.assertTrue(os.path.exists(ruta_temp_export))

        finally:
            if os.path.exists(ruta_temp_plantilla):
                os.remove(ruta_temp_plantilla)
            if os.path.exists(ruta_temp_export):
                os.remove(ruta_temp_export)


if __name__ == "__main__":
    unittest.main()
