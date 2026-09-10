"""Pruebas unitarias para validar las funciones de navegación, búsqueda e integridad del catálogo."""
import unittest
import catalogo_contable as cat


class TestCatalogoContable(unittest.TestCase):

    def test_integridad_clases_y_subgrupos(self):
        """Verifica que existan las 5 clases contables principales y sus subgrupos."""
        clases = cat.listar_clases()
        self.assertEqual(len(clases), 5)
        self.assertTrue(any("Activo" in c for c in clases))
        self.assertTrue(any("Pasivo" in c for c in clases))
        self.assertTrue(any("Capital" in c for c in clases))
        self.assertTrue(any("Ingresos" in c for c in clases))
        self.assertTrue(any("Costos y Gastos" in c for c in clases))

        subgrupos = cat.listar_subgrupos("Activo")
        self.assertTrue(any("Activo Corriente" in k for s in subgrupos.values() for k in s))

    def test_busqueda_cuentas(self):
        """Verifica la búsqueda por código y por nombre en el catálogo."""
        # Búsqueda por código exacto
        encontrados_caja = cat.buscar_cuenta("1101")
        self.assertTrue(len(encontrados_caja) >= 1)
        self.assertEqual(encontrados_caja[0][2], "1101")
        self.assertEqual(encontrados_caja[0][3], "Caja General")

        # Búsqueda de cuentas de nómina
        encontrados_sueldos = cat.buscar_cuenta("5201-01")
        self.assertTrue(len(encontrados_sueldos) >= 1)
        self.assertIn("Sueldos de Administración", encontrados_sueldos[0][3])

        # Búsqueda por palabra clave
        encontrados_igss = cat.buscar_cuenta("IGSS")
        self.assertTrue(len(encontrados_igss) >= 1)
        codigos = [item[2] for item in encontrados_igss]
        self.assertIn("2104-01", codigos)


if __name__ == "__main__":
    unittest.main()
