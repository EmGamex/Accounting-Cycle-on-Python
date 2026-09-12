"""Pruebas unitarias para el subsistema de persistencia unificada."""
from datetime import date
from decimal import Decimal
import json
import os
import shutil
import tempfile
import unittest

from apertura.models import ItemCuentaApertura
from diario.models import LibroDiario, MovimientoLinea, PartidaDiario, TipoOrigenPartida
from planilla.models import DatosEmpleado, ResultadoPlanilla
from persistencia import (
    EjercicioContable,
    FormatoArchivoInvalidoError,
    IntegridadDatosError,
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
        bak_path = self.tmp_path + ".bak"
        if os.path.exists(bak_path):
            os.remove(bak_path)
        tmp_work = self.tmp_path + ".tmp"
        if os.path.exists(tmp_work):
            os.remove(tmp_work)

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

    def test_metadatos_fiscales_guatemala_y_periodo(self):
        """Verifica que los metadatos SAT, contador y fechas de período se persistan con precisión."""
        ej = EjercicioContable(
            nombre_empresa="Importadora Chapina, S.A.",
            nit="1234567-8",
            direccion="Zona 10, Ciudad de Guatemala",
            regimen_tributario="Sobre las Utilidades de Actividades Lucrativas",
            contador_nombre="Juan Perez Perito",
            contador_registro="SAT-998877",
            periodo="2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
            cerrado=True,
        )
        guardar_ejercicio_json(ej, self.tmp_path)

        cargado = cargar_ejercicio_json(self.tmp_path)
        self.assertEqual(cargado.nit, "1234567-8")
        self.assertEqual(cargado.direccion, "Zona 10, Ciudad de Guatemala")
        self.assertEqual(cargado.regimen_tributario, "Sobre las Utilidades de Actividades Lucrativas")
        self.assertEqual(cargado.contador_nombre, "Juan Perez Perito")
        self.assertEqual(cargado.contador_registro, "SAT-998877")
        self.assertEqual(cargado.fecha_inicio, date(2026, 1, 1))
        self.assertEqual(cargado.fecha_fin, date(2026, 12, 31))
        self.assertTrue(cargado.cerrado)

    def test_helpers_derivados_ciclo_contable(self):
        """Verifica que EjercicioContable provea propiedades derivadas para Mayor y Balance."""
        partida = PartidaDiario(
            numero=1,
            fecha=date(2026, 1, 1),
            glosa="Asiento apertura",
            lineas=[
                MovimientoLinea("1101", "Caja General", debe=Decimal("1000.00")),
                MovimientoLinea("3101", "Capital Social", haber=Decimal("1000.00")),
            ],
        )
        ej = EjercicioContable(libro_diario=LibroDiario(partidas=[partida]))
        self.assertTrue(ej.cuadra)

        # Derivar Mayor
        mayor = ej.generar_mayor()
        self.assertIn("1101", mayor.cuentas)
        self.assertIn("3101", mayor.cuentas)

        # Derivar Balance 4 Columnas
        bal4 = ej.generar_balance_4_columnas()
        self.assertEqual(bal4.total_debe, Decimal("1000.00"))
        self.assertEqual(bal4.total_haber, Decimal("1000.00"))
        self.assertTrue(bal4.cuadra)

    def test_escritura_atomica_y_copia_backup(self):
        """Verifica que la escritura sea atómica y genere copia .bak al sobrescribir."""
        ej1 = EjercicioContable(nombre_empresa="Empresa Version 1")
        guardar_ejercicio_json(ej1, self.tmp_path)

        # Comprobar que no quedó .tmp huérfano
        self.assertFalse(os.path.exists(self.tmp_path + ".tmp"))

        # Sobrescribir con versión 2
        ej2 = EjercicioContable(nombre_empresa="Empresa Version 2")
        guardar_ejercicio_json(ej2, self.tmp_path, backup=True)

        # Comprobar que existe el archivo .bak con el contenido previo
        bak_path = self.tmp_path + ".bak"
        self.assertTrue(os.path.exists(bak_path))
        cargado_bak = cargar_ejercicio_json(bak_path)
        self.assertEqual(cargado_bak.nombre_empresa, "Empresa Version 1")

        # Comprobar archivo principal
        cargado_nuevo = cargar_ejercicio_json(self.tmp_path)
        self.assertEqual(cargado_nuevo.nombre_empresa, "Empresa Version 2")

    def test_creacion_automatica_subdirectorios(self):
        """Verifica que guardar_ejercicio_json cree carpetas intermedias si no existen."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sub_path = os.path.join(tmp_dir, "carpeta_nueva", "2026", "ejercicio.json")
            ej = EjercicioContable(nombre_empresa="Empresa Subdirectorios")
            guardar_ejercicio_json(ej, sub_path)
            self.assertTrue(os.path.exists(sub_path))
            cargado = cargar_ejercicio_json(sub_path)
            self.assertEqual(cargado.nombre_empresa, "Empresa Subdirectorios")

    def test_carga_archivo_corrupto_lanza_excepcion(self):
        """Verifica que un archivo con JSON corrupto lance FormatoArchivoInvalidoError."""
        with open(self.tmp_path, "w", encoding="utf-8") as f:
            f.write("{ json no valido: 123 ")

        with self.assertRaises(FormatoArchivoInvalidoError):
            cargar_ejercicio_json(self.tmp_path)

    def test_carga_archivo_no_existente_lanza_error(self):
        """Verifica que cargar un archivo que no existe lance FileNotFoundError."""
        ruta_falsa = self.tmp_path + "_inexistente.json"
        with self.assertRaises(FileNotFoundError):
            cargar_ejercicio_json(ruta_falsa)

    def test_validacion_integridad_descuadre_lanza_error(self):
        """Verifica que si validar_integridad=True y el libro no cuadra, se lance IntegridadDatosError."""
        partida_descuadrada = {
            "version": "1.1",
            "libro_diario": {
                "partidas": [
                    {
                        "numero": 1,
                        "fecha": "2026-01-01",
                        "glosa": "Descuadrada",
                        "lineas": [
                            {"codigo": "1101", "nombre": "Caja", "debe": "100.00", "haber": "0.00"},
                            {"codigo": "3101", "nombre": "Capital", "debe": "0.00", "haber": "50.00"},
                        ],
                    }
                ]
            },
        }
        with open(self.tmp_path, "w", encoding="utf-8") as f:
            json.dump(partida_descuadrada, f)

        with self.assertRaises(IntegridadDatosError):
            cargar_ejercicio_json(self.tmp_path, validar_integridad=True)
