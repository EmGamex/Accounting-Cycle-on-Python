"""Pruebas unitarias para la serialización y persistencia JSON del Libro Diario."""
from datetime import date
from decimal import Decimal
import os
import tempfile
import unittest

from diario import (
    GestorLibroDiario,
    LibroDiario,
    MovimientoLinea,
    PartidaDiario,
    TipoOrigenPartida,
    cargar_libro_json,
    guardar_libro_json,
)


class TestDiarioStorage(unittest.TestCase):

    def setUp(self):
        self.tmp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp_path = self.tmp_file.name
        self.tmp_file.close()

    def tearDown(self):
        if os.path.exists(self.tmp_path):
            os.remove(self.tmp_path)

    def test_guardar_y_cargar_libro_vacio(self):
        """Verifica que un libro sin partidas se guarde y cargue intacto."""
        libro_original = LibroDiario()
        guardar_libro_json(libro_original, self.tmp_path)

        libro_cargado = cargar_libro_json(self.tmp_path)
        self.assertEqual(len(libro_cargado.partidas), 0)
        self.assertEqual(libro_cargado.total_debe, Decimal("0.00"))
        self.assertEqual(libro_cargado.total_haber, Decimal("0.00"))

    def test_guardar_y_cargar_partidas_con_precision_decimal(self):
        """Verifica que fechas, orígenes y montos Decimal no pierdan precisión en JSON."""
        p1 = PartidaDiario(
            numero=1,
            fecha=date(2026, 1, 1),
            glosa="Partida de Apertura inicial",
            origen=TipoOrigenPartida.APERTURA,
            lineas=[
                MovimientoLinea("1101", "Caja General", debe=Decimal("15250.75"), haber=Decimal("0.00")),
                MovimientoLinea("3101", "Capital Social", debe=Decimal("0.00"), haber=Decimal("15250.75")),
            ],
        )
        p2 = PartidaDiario(
            numero=2,
            fecha=date(2026, 1, 15),
            glosa="Compra de mercadería al contado",
            origen=TipoOrigenPartida.COMPRA,
            documento_soporte="FAC-9988",
            lineas=[
                MovimientoLinea("5101", "Compras", debe=Decimal("1000.00"), haber=Decimal("0.00")),
                MovimientoLinea("1105", "IVA por Cobrar", debe=Decimal("120.00"), haber=Decimal("0.00")),
                MovimientoLinea("1101", "Caja General", debe=Decimal("0.00"), haber=Decimal("1120.00")),
            ],
        )

        libro = LibroDiario(partidas=[p1, p2])
        guardar_libro_json(libro, self.tmp_path)

        cargado = cargar_libro_json(self.tmp_path)
        self.assertEqual(len(cargado.partidas), 2)
        self.assertTrue(cargado.cuadra)
        self.assertEqual(cargado.total_debe, Decimal("16370.75"))
        self.assertEqual(cargado.total_haber, Decimal("16370.75"))

        # Validar detalles de partida 1
        partida1 = cargado.partidas[0]
        self.assertEqual(partida1.numero, 1)
        self.assertEqual(partida1.fecha, date(2026, 1, 1))
        self.assertEqual(partida1.origen, TipoOrigenPartida.APERTURA)
        self.assertEqual(partida1.lineas[0].debe, Decimal("15250.75"))

        # Validar detalles de partida 2
        partida2 = cargado.partidas[1]
        self.assertEqual(partida2.documento_soporte, "FAC-9988")
        self.assertEqual(partida2.origen, TipoOrigenPartida.COMPRA)

    def test_gestor_guardar_y_cargar_json(self):
        """Verifica los métodos de persistencia en GestorLibroDiario."""
        gestor = GestorLibroDiario()
        p = PartidaDiario(
            numero=1,
            fecha=date(2026, 2, 1),
            glosa="Asiento simple",
            lineas=[
                MovimientoLinea("1101", "Caja General", debe=Decimal("500.00")),
                MovimientoLinea("1102", "Bancos", haber=Decimal("500.00")),
            ],
        )
        gestor.registrar_partida(p)
        gestor.guardar_json(self.tmp_path)

        nuevo_gestor = GestorLibroDiario()
        nuevo_gestor.cargar_json(self.tmp_path)
        self.assertEqual(len(nuevo_gestor.libro.partidas), 1)
        self.assertEqual(nuevo_gestor.siguiente_numero, 2)
