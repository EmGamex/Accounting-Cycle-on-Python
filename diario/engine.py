"""Motor de reglas, correlativos y validación del Libro Diario."""
from decimal import Decimal
from typing import Dict, List, Tuple

import catalogo_contable
from .exceptions import CorrelativoError, CuentaInvalidaError, DescuadrePartidaError, FechaInvalidaError
from .models import LibroDiario, MovimientoLinea, PartidaDiario
from .storage import cargar_libro_json, guardar_libro_json


class GestorLibroDiario:
    """Motor de gestión contable para el Libro Diario."""

    def __init__(self, estricto_cronologico: bool = False):
        self.libro = LibroDiario()
        self.estricto_cronologico = estricto_cronologico
        self._catalogo_codigos: Dict[str, str] = self._cargar_codigos_catalogo()

    def _cargar_codigos_catalogo(self) -> Dict[str, str]:
        """Indexa todos los códigos y nombres del catálogo central para búsqueda O(1)."""
        return {
            codigo.strip(): nombre.strip()
            for _, _, codigo, nombre in catalogo_contable.listar_cuentas()
        }

    @property
    def siguiente_numero(self) -> int:
        """Retorna el siguiente número correlativo esperado."""
        return len(self.libro.partidas) + 1

    def validar_cuenta(self, codigo: str) -> bool:
        """Verifica si un código contable existe en el catálogo oficial."""
        return codigo.strip() in self._catalogo_codigos

    def registrar_partida(
        self,
        partida: PartidaDiario,
        validar_catalogo: bool = True,
        auto_correlativo: bool = False,
    ) -> PartidaDiario:
        """Valida y registra formalmente una partida en el libro diario.

        Raises:
            DescuadrePartidaError: Si el asiento no cumple con el principio de partida doble.
            CorrelativoError: Si el número de asiento no sigue la secuencia estricta.
            FechaInvalidaError: Si la fecha es anterior a la última registrada (en modo estricto).
            CuentaInvalidaError: Si alguna cuenta no existe en el catálogo contable.
        """
        lineas = partida.lineas
        if not lineas:
            raise DescuadrePartidaError(
                f"La partida No. {partida.numero} no contiene líneas de movimiento contable."
            )

        if not partida.cuadra:
            raise DescuadrePartidaError(
                f"Partida No. {partida.numero} descuadrada: "
                f"Debe = Q{partida.total_debe}, Haber = Q{partida.total_haber}, "
                f"Diferencia = Q{partida.diferencia}"
            )

        esperado = self.siguiente_numero
        if auto_correlativo or partida.numero <= 0:
            partida.numero = esperado
        elif partida.numero != esperado:
            raise CorrelativoError(
                f"Error correlativo en Libro Diario: se esperaba Partida No. {esperado}, "
                f"pero se intentó registrar Partida No. {partida.numero}."
            )

        partidas = self.libro.partidas
        if partidas:
            ultima_fecha = partidas[-1].fecha
            if self.estricto_cronologico and partida.fecha < ultima_fecha:
                raise FechaInvalidaError(
                    f"Inconsistencia cronológica: la partida No. {partida.numero} tiene fecha "
                    f"{partida.fecha:%d/%m/%Y}, anterior a la última registrada "
                    f"({ultima_fecha:%d/%m/%Y})."
                )

        if validar_catalogo:
            for linea in lineas:
                # Se permite cuenta especial o auxiliar siempre que el código base exista
                if not self.validar_cuenta(linea.codigo):
                    raise CuentaInvalidaError(
                        f"La cuenta con código '{linea.codigo.strip()}' ({linea.nombre}) no existe "
                        f"en el Catálogo Contable Central."
                    )

        partidas.append(partida)
        return partida

    def totales(self) -> Tuple[Decimal, Decimal]:
        """Retorna una tupla (Total Debe, Total Haber) acumulada del libro."""
        return self.libro.total_debe, self.libro.total_haber

    def obtener_partidas(self) -> List[PartidaDiario]:
        """Retorna la lista de todas las partidas registradas."""
        return list(self.libro.partidas)

    def filtrar_por_cuenta(self, codigo_o_nombre: str) -> List[Tuple[PartidaDiario, MovimientoLinea]]:
        """Busca y retorna todos los movimientos asociados a una cuenta dada."""
        termino = codigo_o_nombre.strip().lower()
        return [
            (p, l)
            for p in self.libro.partidas
            for l in p.lineas
            if termino == l.codigo.lower() or termino in l.nombre.lower()
        ]

    def guardar_json(self, ruta_archivo: str) -> None:
        """Persiste el libro actual en formato JSON."""
        guardar_libro_json(self.libro, ruta_archivo)

    def cargar_json(self, ruta_archivo: str) -> None:
        """Carga y reemplaza las partidas actuales con las de un archivo JSON."""
        self.libro = cargar_libro_json(ruta_archivo)
