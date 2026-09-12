"""Motor de agrupación, pase automático y validación del Libro Mayor."""
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import catalogo_contable
from .exceptions import DescuadreMayorError, LibroDiarioVacioError
from .models import CuentaMayor, LibroMayor, MovimientoMayor

if TYPE_CHECKING:
    from diario.models import LibroDiario


def mayorizar_libro_diario(
    libro_diario: Any,
    validar_cuadre_diario: bool = True,
    permitir_vacio: bool = False,
) -> LibroMayor:
    """Transforma y agrupa todas las partidas del Libro Diario en cuentas del Libro Mayor.

    Args:
        libro_diario: Objeto LibroDiario con las partidas del período.
        validar_cuadre_diario: Si es True, exige que el libro diario cuadre antes de mayorizar.
        permitir_vacio: Si es True, retorna un LibroMayor vacío si no hay partidas.

    Returns:
        Instancia de LibroMayor completamente estructurada y con saldos determinados.

    Raises:
        LibroDiarioVacioError: Si no hay partidas y permitir_vacio es False.
        DescuadreMayorError: Si el libro diario está descuadrado o el mayor resultante no cuadra.
    """
    partidas = getattr(libro_diario, "partidas", [])
    if not partidas:
        if permitir_vacio:
            return LibroMayor()
        raise LibroDiarioVacioError("No se puede mayorizar: el Libro Diario no tiene partidas registradas.")

    cuadra_diario = getattr(libro_diario, "cuadra", True)
    diferencia_diario = getattr(libro_diario, "diferencia", Decimal("0.00"))

    if validar_cuadre_diario and not cuadra_diario:
        raise DescuadreMayorError(
            f"El Libro Diario está descuadrado (Diferencia: Q{diferencia_diario}). "
            "Corrija los asientos antes de realizar el pase al Mayor."
        )

    # Índice O(1) con nomenclatura oficial NIIF/SAT para normalizar nombres
    nombres_catalogo: Dict[str, str] = {
        cod.strip(): nom.strip()
        for _, _, cod, nom in catalogo_contable.listar_cuentas()
    }

    cuentas_dict: Dict[str, CuentaMayor] = {}

    for partida in partidas:
        for linea in partida.lineas:
            cod = linea.codigo.strip()
            # Prioriza la denominación central del catálogo NIIF/SAT; mantiene la de la partida si es auxiliar
            nombre_linea = linea.nombre.strip() if getattr(linea, "nombre", None) else cod
            nombre = nombres_catalogo.get(cod) or nombre_linea or cod

            if cod not in cuentas_dict:
                cuentas_dict[cod] = CuentaMayor(codigo=cod, nombre=nombre)

            mov = MovimientoMayor(
                numero_partida=partida.numero,
                fecha=partida.fecha,
                concepto=partida.glosa,
                debe=linea.debe,
                haber=linea.haber,
                documento_soporte=partida.documento_soporte,
            )
            cuentas_dict[cod].movimientos.append(mov)

    libro_mayor = LibroMayor(cuentas=cuentas_dict)

    # Verificación de partida doble: sumas iguales al Diario y balance de saldos deudores vs acreedores
    total_debe_diario = libro_diario.total_debe
    total_haber_diario = libro_diario.total_haber

    if libro_mayor.total_debe != total_debe_diario:
        raise DescuadreMayorError(
            f"Inconsistencia en pase al Mayor: Suma Debe Mayor (Q{libro_mayor.total_debe}) "
            f"no coincide con Suma Debe Diario (Q{total_debe_diario})."
        )
    if libro_mayor.total_haber != total_haber_diario:
        raise DescuadreMayorError(
            f"Inconsistencia en pase al Mayor: Suma Haber Mayor (Q{libro_mayor.total_haber}) "
            f"no coincide con Suma Haber Diario (Q{total_haber_diario})."
        )

    if validar_cuadre_diario and not libro_mayor.cuadra:
        raise DescuadreMayorError(
            f"El Libro Mayor resultante no cumple con la partida doble: "
            f"Saldos Deudores (Q{libro_mayor.total_saldos_deudores}) != "
            f"Saldos Acreedores (Q{libro_mayor.total_saldos_acreedores})."
        )

    return libro_mayor


class GestorLibroMayor:
    """Controlador y servicio de consulta del Libro Mayor."""

    def __init__(self, libro_diario: Optional[Any] = None):
        self._libro_diario: Optional[Any] = libro_diario
        self._libro_mayor: Optional[LibroMayor] = None

    @property
    def libro_mayor(self) -> LibroMayor:
        """Retorna el libro mayor activo o lo genera a partir del diario."""
        if self._libro_mayor is None:
            self.sincronizar()
        return self._libro_mayor or LibroMayor()

    def sincronizar(self) -> LibroMayor:
        """Re-mayoriza los datos actuales del Libro Diario."""
        if self._libro_diario is None or not getattr(self._libro_diario, "partidas", None):
            self._libro_mayor = LibroMayor()
        else:
            self._libro_mayor = mayorizar_libro_diario(
                self._libro_diario,
                validar_cuadre_diario=False,
                permitir_vacio=True,
            )
        return self._libro_mayor

    def obtener_cuenta(self, codigo: str) -> Optional[CuentaMayor]:
        """Obtiene una cuenta por su código contable."""
        return self.libro_mayor.obtener_cuenta(codigo)

    def buscar_cuentas(self, termino: str) -> List[CuentaMayor]:
        """Busca cuentas en el mayor por coincidencia en código o nombre."""
        return self.libro_mayor.buscar_cuentas(termino)
