"""Motor de reglas, correlativos y validación del Libro Diario."""
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import catalogo_contable
from config import CERO_MONETARIO, FORMATO_FECHA, SIMBOLO_MONEDA
from .exceptions import CorrelativoError, CuentaInvalidaError, DescuadrePartidaError, FechaInvalidaError
from .models import LibroDiario, MovimientoLinea, PartidaDiario
from .storage import cargar_libro_json, guardar_libro_json

CORRELATIVO_INICIAL: int = 1
CORRELATIVO_MINIMO_VALIDO: int = 1


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
        return len(self.libro.partidas) + CORRELATIVO_INICIAL

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
                f"Debe = {SIMBOLO_MONEDA}{partida.total_debe}, "
                f"Haber = {SIMBOLO_MONEDA}{partida.total_haber}, "
                f"Diferencia = {SIMBOLO_MONEDA}{partida.diferencia}"
            )

        esperado = self.siguiente_numero
        if auto_correlativo or partida.numero < CORRELATIVO_MINIMO_VALIDO:
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
                    f"{partida.fecha.strftime(FORMATO_FECHA)}, anterior a la última registrada "
                    f"({ultima_fecha.strftime(FORMATO_FECHA)})."
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

    def obtener_partida(self, numero: int) -> Optional[PartidaDiario]:
        """Busca y retorna una partida por su número correlativo."""
        for p in self.libro.partidas:
            if p.numero == numero:
                return p
        return None

    def actualizar_partida(
        self,
        numero: int,
        nueva_partida: PartidaDiario,
        validar_catalogo: bool = True,
    ) -> PartidaDiario:
        """Actualiza una partida existente asegurando cuadre y validación de catálogo."""
        idx_encontrado = -1
        for idx, p in enumerate(self.libro.partidas):
            if p.numero == numero:
                idx_encontrado = idx
                break

        if idx_encontrado == -1:
            raise CorrelativoError(f"No existe la partida No. {numero} para actualizar.")

        if not nueva_partida.cuadra:
            raise DescuadrePartidaError(
                f"La partida No. {numero} a actualizar está descuadrada: "
                f"Debe = {SIMBOLO_MONEDA}{nueva_partida.total_debe}, "
                f"Haber = {SIMBOLO_MONEDA}{nueva_partida.total_haber}."
            )

        if validar_catalogo:
            for linea in nueva_partida.lineas:
                if not self.validar_cuenta(linea.codigo):
                    raise CuentaInvalidaError(
                        f"La cuenta con código '{linea.codigo.strip()}' ({linea.nombre}) no existe en el Catálogo."
                    )

        nueva_partida.numero = numero
        self.libro.partidas[idx_encontrado] = nueva_partida
        return nueva_partida

    def eliminar_partida(self, numero: int, recorrelacionar: bool = True) -> bool:
        """Elimina una partida y opcionalmente re-correlaciona las posteriores."""
        idx_encontrado = -1
        for idx, p in enumerate(self.libro.partidas):
            if p.numero == numero:
                idx_encontrado = idx
                break

        if idx_encontrado == -1:
            return False

        del self.libro.partidas[idx_encontrado]

        if recorrelacionar:
            for i, p in enumerate(self.libro.partidas, start=1):
                p.numero = i

        return True

    def mover_partida(self, origen: int, destino: int) -> bool:
        """Mueve una partida del correlativo origen al destino y re-indexa la secuencia."""
        total = len(self.libro.partidas)
        if not (1 <= origen <= total) or not (1 <= destino <= total):
            return False

        if origen == destino:
            return True

        partida = self.libro.partidas.pop(origen - 1)
        self.libro.partidas.insert(destino - 1, partida)

        for i, p in enumerate(self.libro.partidas, start=1):
            p.numero = i

        return True

    def ordenar_partidas_cronologicamente(self) -> None:
        """Ordena todas las partidas por fecha ascendente de forma estable y re-indexa correlativos."""
        self.libro.partidas.sort(key=lambda p: p.fecha)
        for i, p in enumerate(self.libro.partidas, start=1):
            p.numero = i

    def totales(self) -> Tuple[Decimal, Decimal]:
        """Retorna una tupla (Total Debe, Total Haber) acumulada del libro."""
        return self.libro.total_debe, self.libro.total_haber

    def obtener_partidas(self) -> List[PartidaDiario]:
        """Retorna la lista de todas las partidas registradas."""
        return list(self.libro.partidas)

    def agrupar_movimientos_por_cuenta(self) -> Dict[str, List[Tuple[PartidaDiario, MovimientoLinea]]]:
        """Agrupa eficientemente en O(N) todos los movimientos del libro indexados por código de cuenta."""
        agrupado: Dict[str, List[Tuple[PartidaDiario, MovimientoLinea]]] = defaultdict(list)
        for partida in self.libro.partidas:
            for linea in partida.lineas:
                agrupado[linea.codigo.strip()].append((partida, linea))
        return dict(agrupado)

    def totales_por_cuenta(self) -> Dict[str, Dict[str, Decimal]]:
        """Calcula en O(N) la sumatoria acumulada de Debe y Haber agrupada por cuenta."""
        resumen: Dict[str, Dict[str, Decimal]] = defaultdict(
            lambda: {"debe": CERO_MONETARIO, "haber": CERO_MONETARIO}
        )
        for partida in self.libro.partidas:
            for linea in partida.lineas:
                cod = linea.codigo.strip()
                resumen[cod]["debe"] += linea.debe
                resumen[cod]["haber"] += linea.haber
        return dict(resumen)

    def filtrar_por_cuenta(self, codigo_o_nombre: str) -> List[Tuple[PartidaDiario, MovimientoLinea]]:
        """Busca y retorna todos los movimientos asociados a una cuenta dada."""
        termino = codigo_o_nombre.strip().lower()
        return [
            (p, l)
            for p in self.libro.partidas
            for l in p.lineas
            if termino == l.codigo.lower() or termino in l.nombre.lower()
        ]

    def obtener_saldos_iva(self) -> Tuple[Decimal, Decimal]:
        """Calcula los saldos netos actuales de Crédito Fiscal (1107) y Débito Fiscal (2105).

        Crédito Fiscal (Activo): Debe - Haber
        Débito Fiscal (Pasivo): Haber - Debe

        Returns:
            Tupla (saldo_credito, saldo_debito).
        """
        totales = self.totales_por_cuenta()
        cod_credito = catalogo_contable.Cuenta.IVA_CREDITO.value
        cod_debito = catalogo_contable.Cuenta.IVA_DEBITO.value

        mov_credito = totales.get(cod_credito, {"debe": CERO_MONETARIO, "haber": CERO_MONETARIO})
        mov_debito = totales.get(cod_debito, {"debe": CERO_MONETARIO, "haber": CERO_MONETARIO})

        saldo_credito = mov_credito["debe"] - mov_credito["haber"]
        saldo_debito = mov_debito["haber"] - mov_debito["debe"]

        return max(CERO_MONETARIO, saldo_credito), max(CERO_MONETARIO, saldo_debito)

    def puede_regularizar_iva(self) -> bool:
        """Determina si ambas cuentas de IVA cuentan con saldo positivo compensable."""
        credito, debito = self.obtener_saldos_iva()
        return credito > CERO_MONETARIO and debito > CERO_MONETARIO

    def guardar_json(self, ruta_archivo: str) -> None:
        """Persiste el libro actual en formato JSON."""
        guardar_libro_json(self.libro, ruta_archivo)

    def cargar_json(self, ruta_archivo: str) -> None:
        """Carga y reemplaza las partidas actuales con las de un archivo JSON."""
        self.libro = cargar_libro_json(ruta_archivo)
