"""Generación del reporte consolidado del Libro Diario de Operaciones."""
from typing import Any, List

from .formato import centrar_titulo, formato_moneda, linea_doble
from .partidas import generar_texto_partida


def generar_texto_libro_diario(
    libro: Any,
    empresa: str = "EMPRESA GUATEMALTECA, S.A.",
    ancho: int = 80,
) -> str:
    """Genera el texto formal completo del Libro Diario con todas sus partidas y cierre general.

    Args:
        libro: Objeto LibroDiario que agrupa las partidas del período.
        empresa: Razón social o nombre comercial de la empresa.
        ancho: Ancho en caracteres del reporte.

    Returns:
        Cadena con el Libro Diario completo listo para emisión o guardado.
    """
    bloques: List[str] = []

    # Encabezado formal del libro
    bloques.append(linea_doble(ancho))
    bloques.append(centrar_titulo(empresa, ancho))
    bloques.append(centrar_titulo("LIBRO DIARIO DE OPERACIONES", ancho))
    bloques.append(centrar_titulo("(Cifras expresadas en Quetzales - Q)", ancho))
    bloques.append(linea_doble(ancho))
    bloques.append("")

    if not libro.partidas:
        bloques.append(centrar_titulo("No hay partidas registradas en el Libro Diario.", ancho))
        return "\n".join(bloques)

    for p in libro.partidas:
        bloques.append(generar_texto_partida(p, ancho=ancho))
        bloques.append("")

    # Resumen y cierre del Libro Diario
    bloques.append(linea_doble(ancho))
    bloques.append(centrar_titulo("RESUMEN GENERAL DEL LIBRO DIARIO", ancho))
    bloques.append(linea_doble(ancho))
    bloques.append(f"Total de Partidas Registradas: {len(libro.partidas)}")
    total_d = formato_moneda(libro.total_debe)
    total_h = formato_moneda(libro.total_haber)
    bloques.append(f"Suma Total Acumulada Debe:    {total_d:>20}")
    bloques.append(f"Suma Total Acumulada Haber:   {total_h:>20}")
    bloques.append(f"Estado de Cuadre:             {'CUADRE EXACTO' if libro.cuadra else 'DESCUADRADO':>20}")
    bloques.append(linea_doble(ancho))

    return "\n".join(bloques)
