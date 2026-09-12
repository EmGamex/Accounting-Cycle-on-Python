"""Pruebas unitarias para el subsistema de persistencia unificada."""
from datetime import date
from decimal import Decimal
import json
import os
import tempfile
import unittest

from apertura.models import ItemCuentaApertura
from diario.models import LibroDiario, MovimientoLinea, PartidaDiario, TipoOrigenPartida
from planilla.models import DatosEmpleado, ResultadoPlanilla
from persistencia import (
    EjercicioContable,
    cargar_ejercicio_json,
    ejercicio_a_dict,
    ejercicio_de_dict,
    guardar_ejercicio_json,
)


class TestPersistenciaUnificada(unittest.TestCase):

    def setUp(self):
        self.tmp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp_path = self.tmp_file.name
        self.tmp_file.close()

    def tearDown(self):
        if os.path.exists(self.tmp_path):
            os.remove(self.tmp_path)

    def test_ejercicio_vacio_guardar_y_cargar(self):
        """Verifica que un ejercicio vacío se guarde y recupere intacto."""
        ej = EjercicioContable(
            nombre_empresa="Comercial La Paz",
            periodo="2026",
        )
        guardar_ejercicio_json(ej, self.tmp_path)

        cargado = cargar_ejercicio_json(self.tmp_path)
        self.assertEqual(cargado.nombre_empresa, "Comercial La Paz")
        self.assertEqual(cargado.periodo, "2026")
        self.assertEqual(len(cargado.items_apertura), 0)
        self.assertEqual(len(cargado.libro_diario.partidas), 0)
        self.assertEqual(len(cargado.empleados), 0)
        self.assertEqual(len(cargado.planillas), 0)

    def test_ejercicio_completo_guardar_y_cargar(self):
        """Verifica que apertura, diario y nómina se persistan juntos sin pérdida de precisión."""
        # 1. Apertura
        item_caja = ItemCuentaApertura(
            codigo="1101",
            nombre="Caja General",
            monto=Decimal("25000.50"),
            clase="Activo",
            subgrupo="Corriente",
        )
        # 2. Diario
        partida = PartidaDiario(
            numero=1,
            fecha=date(2026, 1, 1),
            glosa="Asiento de apertura",
            origen=TipoOrigenPartida.APERTURA,
            lineas=[
                MovimientoLinea("1101", "Caja General", debe=Decimal("25000.50")),
                MovimientoLinea("3101", "Capital Social", haber=Decimal("25000.50")),
            ],
        )
        libro = LibroDiario(partidas=[partida])
        # 3. Empleados y planillas
        empleado = DatosEmpleado(
            nombre="Elena Gomez",
            departamento="Ventas",
            sueldo_base=Decimal("7000.00"),
            ventas=Decimal("15000.00"),
            pct_comision=Decimal("5.00"),
            isr_manual=Decimal("250.00"),
        )
        planilla = ResultadoPlanilla(
            empleado="Elena Gomez",
            departamento="Ventas",
            sueldo_base=Decimal("7000.00"),
            comisiones=Decimal("750.00"),
            horas_extras_trabajadas=Decimal("0.00"),
            sueldo_extraordinario=Decimal("0.00"),
            bonificacion_ley=Decimal("250.00"),
            total_afecto_igss=Decimal("7750.00"),
            total_devengado=Decimal("8000.00"),
            descuento_igss=Decimal("374.33"),
            descuento_isr=Decimal("250.00"),
            prestamos_deudas=Decimal("0.00"),
            otros_descuentos=Decimal("0.00"),
            total_descuentos=Decimal("624.33"),
            liquido_recibir=Decimal("7375.67"),
        )

        ejercicio = EjercicioContable(
            nombre_empresa="Distribuidora Global, S.A.",
            periodo="2026",
            items_apertura=[item_caja],
            libro_diario=libro,
            empleados=[empleado],
            planillas=[planilla],
        )

        guardar_ejercicio_json(ejercicio, self.tmp_path)
        cargado = cargar_ejercicio_json(self.tmp_path)

        # Validaciones
        self.assertEqual(cargado.nombre_empresa, "Distribuidora Global, S.A.")
        self.assertEqual(len(cargado.items_apertura), 1)
        self.assertEqual(cargado.items_apertura[0].monto, Decimal("25000.50"))

        self.assertEqual(len(cargado.libro_diario.partidas), 1)
        self.assertEqual(cargado.libro_diario.partidas[0].lineas[0].debe, Decimal("25000.50"))

        self.assertEqual(len(cargado.empleados), 1)
        self.assertEqual(cargado.empleados[0].sueldo_base, Decimal("7000.00"))
        self.assertEqual(cargado.empleados[0].isr_manual, Decimal("250.00"))

        self.assertEqual(len(cargado.planillas), 1)
        self.assertEqual(cargado.planillas[0].liquido_recibir, Decimal("7375.67"))

    def test_compatibilidad_retroactiva_libro_diario_legado(self):
        """Verifica que un archivo que solo tenga partidas (formato legado) se cargue como EjercicioContable."""
        legado_data = {
            "formato_version": "1.0",
            "total_debe": "500.00",
            "total_haber": "500.00",
            "cuadra": True,
            "partidas": [
                {
                    "numero": 1,
                    "fecha": "2026-03-01",
                    "glosa": "Pago servicio",
                    "origen": "manual",
                    "documento_soporte": None,
                    "lineas": [
                        {"codigo": "5102", "nombre": "Servicios", "debe": "500.00", "haber": "0.00"},
                        {"codigo": "1101", "nombre": "Caja General", "debe": "0.00", "haber": "500.00"},
                    ],
                }
            ],
        }

        with open(self.tmp_path, "w", encoding="utf-8") as f:
            json.dump(legado_data, f)

        cargado = cargar_ejercicio_json(self.tmp_path)
        self.assertEqual(len(cargado.libro_diario.partidas), 1)
        self.assertEqual(cargado.libro_diario.partidas[0].glosa, "Pago servicio")
        self.assertEqual(cargado.libro_diario.total_debe, Decimal("500.00"))
