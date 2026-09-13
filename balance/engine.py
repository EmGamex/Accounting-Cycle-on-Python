"""Motor analítico de cálculo para el Balance de 4 Columnas y Balance de Situación General de Cierre."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

import catalogo_contable
from mayor.engine import GestorLibroMayor, mayorizar_libro_diario
from mayor.models import CuentaMayor, LibroMayor, NaturalezaSaldo

from .exceptions import BalanceVacioError, DescuadreBalanceError, EcuacionPatrimonialError
from .models import (
    Balance4Columnas,
    BalanceSituacionGeneral,
    FilaBalance4Columnas,
    ItemBalanceGeneral,
    ResumenResultados,
    TWO_PLACES,
)


def _obtener_catalogo_clasificacion() -> Dict[str, Dict[str, Any]]:
    """Indexa el catálogo central para mapear código -> (clase, subgrupo, nombre, es_regularizadora)."""
    resultado: Dict[str, Dict[str, Any]] = {}
    for clase, subgrupos in catalogo_contable.catalogo_cuentas.items():
        for subgrupo, cuentas in subgrupos.items():
            for cod, nombre in cuentas.items():
                cod_str = str(cod).strip()
                es_reg = "-R" in cod_str or "(-)" in nombre or cod_str.startswith("1205") or cod_str.startswith("1210")
                resultado[cod_str] = {
                    "clase": clase,
                    "subgrupo": subgrupo,
                    "nombre": nombre.replace("(-)", "").strip(),
                    "es_regularizadora": es_reg,
                }
    return resultado


def generar_balance_4_columnas(
    origen: Any,
    validar_cuadre: bool = True,
    permitir_vacio: bool = False,
    empresa: str = "Empresa Ejemplo, S.A.",
    periodo: str = "2026",
    fecha_emision: Optional[date] = None,
) -> Balance4Columnas:
    """Genera la matriz del Balance de Comprobación y Saldos (4 Columnas).

    Args:
        origen: Instancia de LibroMayor, GestorLibroMayor, LibroDiario o GestorLibroDiario.
        validar_cuadre: Exige que el balance cumpla con la doble condición de partida doble.
        permitir_vacio: Si es True, no levanta error si no hay cuentas.
        empresa: Razón social de la entidad.
        periodo: Ejercicio contable reportado.
        fecha_emision: Fecha de emisión del estado financiero.

    Returns:
        Instancia de Balance4Columnas con filas y sumas calculadas.

    Raises:
        BalanceVacioError: Si no hay cuentas y permitir_vacio es False.
        DescuadreBalanceError: Si sumas o saldos no cuadran.
    """
    if isinstance(origen, LibroMayor):
        mayor = origen
    elif isinstance(origen, GestorLibroMayor):
        mayor = origen.sincronizar()
    elif hasattr(origen, "libro"):  # GestorLibroDiario
        mayor = mayorizar_libro_diario(origen.libro, validar_cuadre_diario=False, permitir_vacio=True)
    elif hasattr(origen, "partidas"):  # LibroDiario
        mayor = mayorizar_libro_diario(origen, validar_cuadre_diario=False, permitir_vacio=True)
    else:
        mayor = LibroMayor()

    if not mayor.cuentas:
        if permitir_vacio:
            return Balance4Columnas(
                empresa=empresa,
                periodo=periodo,
                fecha_emision=fecha_emision or date.today(),
            )
        raise BalanceVacioError("No se puede generar el Balance de 4 Columnas: no existen cuentas en el Libro Mayor.")

    clasif_cat = _obtener_catalogo_clasificacion()
    filas: List[FilaBalance4Columnas] = []

    for numero, cuenta in enumerate(mayor.cuentas_ordenadas, start=1):
        cod = cuenta.codigo.strip()
        info_cat = clasif_cat.get(cod)

        if info_cat:
            clase = info_cat["clase"]
            subgrupo = info_cat["subgrupo"]
            nombre = info_cat["nombre"]
            es_reg = info_cat["es_regularizadora"]
        else:
            clase = "1. Activo" if cod.startswith("1") else (
                "2. Pasivo" if cod.startswith("2") else (
                    "3. Capital / Patrimonio" if cod.startswith("3") else (
                        "4. Ingresos" if cod.startswith("4") else "5. Costos y Gastos"
                    )
                )
            )
            subgrupo = "General"
            nombre = cuenta.nombre
            es_reg = "-R" in cod or cod.startswith("1205") or cod.startswith("1210")

        fila = FilaBalance4Columnas(
            numero=numero,
            codigo=cod,
            nombre=nombre,
            suma_debe=cuenta.total_debe,
            suma_haber=cuenta.total_haber,
            saldo_deudor=cuenta.saldo_deudor,
            saldo_acreedor=cuenta.saldo_acreedor,
            clase=clase,
            subgrupo=subgrupo,
            es_regularizadora=es_reg,
            es_saldo_anomalo=cuenta.es_saldo_anomalo,
        )
        filas.append(fila)

    balance_4c = Balance4Columnas(
        empresa=empresa,
        periodo=periodo,
        fecha_emision=fecha_emision or date.today(),
        filas=filas,
    )

    if validar_cuadre and not balance_4c.cuadra:
        raise DescuadreBalanceError(
            f"El Balance de 4 Columnas no cuadra: "
            f"Sumas Debe ({balance_4c.total_debe}) vs Haber ({balance_4c.total_haber}) "
            f"[Dif: {balance_4c.diferencia_sumas}], "
            f"Saldos Deudores ({balance_4c.total_saldos_deudores}) vs "
            f"Acreedores ({balance_4c.total_saldos_acreedores}) "
            f"[Dif: {balance_4c.diferencia_saldos}]."
        )

    return balance_4c


def calcular_estado_resultados(balance_4c: Balance4Columnas) -> ResumenResultados:
    """Calcula las cifras del Estado de Resultados a partir de las cuentas nominales (4 y 5)."""
    ingresos = Decimal("0.00")
    costos = Decimal("0.00")
    gastos = Decimal("0.00")

    for f in balance_4c.filas:
        cod = f.codigo
        if cod.startswith("4"):
            # Clase 4: Ingresos (habitualmente saldo acreedor; 4103 Devoluciones tiene saldo deudor)
            if cod.startswith("4103"):
                ingresos -= f.saldo_deudor
            else:
                ingresos += f.saldo_acreedor
        elif cod.startswith("5"):
            # Clase 5: Costos y Gastos (habitualmente saldo deudor)
            if cod.startswith("51"):
                costos += f.saldo_deudor
            else:
                gastos += f.saldo_deudor

    resultado = (ingresos - (costos + gastos)).quantize(TWO_PLACES)
    es_ganancia = resultado >= Decimal("0.00")

    return ResumenResultados(
        total_ingresos=ingresos.quantize(TWO_PLACES),
        total_costos=costos.quantize(TWO_PLACES),
        total_gastos=gastos.quantize(TWO_PLACES),
        resultado_ejercicio=resultado,
        es_ganancia=es_ganancia,
    )


def generar_balance_general(
    balance_4c_o_origen: Any,
    empresa: str = "Empresa Ejemplo, S.A.",
    periodo: str = "2026",
    fecha_emision: Optional[date] = None,
    validar_cuadre: bool = True,
) -> BalanceSituacionGeneral:
    """Genera el Balance de Situación General de Cierre clasificado (Activo, Pasivo, Patrimonio).

    Toma los saldos de cuentas reales e integra el Resultado del Ejercicio derivado
    de las cuentas nominales.
    """
    if isinstance(balance_4c_o_origen, Balance4Columnas):
        balance_4c = balance_4c_o_origen
    else:
        balance_4c = generar_balance_4_columnas(
            balance_4c_o_origen,
            validar_cuadre=validar_cuadre,
            empresa=empresa,
            periodo=periodo,
            fecha_emision=fecha_emision,
        )

    resumen_res = calcular_estado_resultados(balance_4c)
    estructura: Dict[str, Dict[str, List[ItemBalanceGeneral]]] = defaultdict(lambda: defaultdict(list))

    total_act_corr = Decimal("0.00")
    total_act_no_corr = Decimal("0.00")
    total_pas_corr = Decimal("0.00")
    total_pas_no_corr = Decimal("0.00")

    patrimonio_capital = Decimal("0.00")
    patrimonio_reservas = Decimal("0.00")
    patrimonio_resultados_acum = Decimal("0.00")
    resultado_ejercicio_asentado = Decimal("0.00")
    tiene_resultado_asentado = False

    for f in balance_4c.filas:
        cod = f.codigo
        # Ignorar cuentas de ingresos y costos/gastos que ya se consolidan en el resultado del ejercicio
        if cod.startswith("4") or cod.startswith("5"):
            continue

        # 1. Activo
        if cod.startswith("1"):
            # Determinar corriente vs no corriente
            es_no_corriente = cod.startswith("12")
            subgrupo = "1.2 Activo No Corriente" if es_no_corriente else "1.1 Activo Corriente"
            clase = "1. Activo"

            if f.es_regularizadora:
                # Regularizadoras (depreciación acumulada, estimación incobrables): restan del activo
                monto = f.saldo_acreedor if f.saldo_acreedor > Decimal("0.00") else f.saldo_deudor
                item = ItemBalanceGeneral(codigo=cod, nombre=f.nombre, monto=monto, es_regularizadora=True)
                estructura[clase][subgrupo].append(item)
                if es_no_corriente:
                    total_act_no_corr -= monto
                else:
                    total_act_corr -= monto
            else:
                monto = f.saldo_deudor if f.saldo_deudor > Decimal("0.00") else -f.saldo_acreedor
                item = ItemBalanceGeneral(codigo=cod, nombre=f.nombre, monto=monto, es_regularizadora=False)
                estructura[clase][subgrupo].append(item)
                if es_no_corriente:
                    total_act_no_corr += monto
                else:
                    total_act_corr += monto

        # 2. Pasivo
        elif cod.startswith("2"):
            es_no_corriente = cod.startswith("22")
            subgrupo = "2.2 Pasivo No Corriente" if es_no_corriente else "2.1 Pasivo Corriente"
            clase = "2. Pasivo"

            monto = f.saldo_acreedor if f.saldo_acreedor > Decimal("0.00") else -f.saldo_deudor
            item = ItemBalanceGeneral(codigo=cod, nombre=f.nombre, monto=monto, es_regularizadora=False)
            estructura[clase][subgrupo].append(item)
            if es_no_corriente:
                total_pas_no_corr += monto
            else:
                total_pas_corr += monto

        # 3. Patrimonio / Capital
        elif cod.startswith("3"):
            clase = "3. Capital / Patrimonio"
            subgrupo = "3.1 Capital Contable"
            if cod == "3101":
                monto = f.saldo_acreedor
                patrimonio_capital += monto
                item = ItemBalanceGeneral(codigo=cod, nombre=f.nombre, monto=monto)
                estructura[clase][subgrupo].append(item)
            elif cod == "3102":
                monto = f.saldo_acreedor
                patrimonio_reservas += monto
                item = ItemBalanceGeneral(codigo=cod, nombre=f.nombre, monto=monto)
                estructura[clase][subgrupo].append(item)
            elif cod in ("3103", "3104"):
                if cod == "3104":  # Pérdidas acumuladas (deudora)
                    monto = f.saldo_deudor
                    patrimonio_resultados_acum -= monto
                    item = ItemBalanceGeneral(codigo=cod, nombre=f.nombre, monto=monto, es_regularizadora=True)
                else:
                    monto = f.saldo_acreedor
                    patrimonio_resultados_acum += monto
                    item = ItemBalanceGeneral(codigo=cod, nombre=f.nombre, monto=monto)
                estructura[clase][subgrupo].append(item)
            elif cod == "3105":
                # Si ya existía asiento de cierre previo
                tiene_resultado_asentado = True
                resultado_ejercicio_asentado = f.saldo_acreedor - f.saldo_deudor
                item = ItemBalanceGeneral(codigo=cod, nombre=f.nombre, monto=abs(resultado_ejercicio_asentado))
                estructura[clase][subgrupo].append(item)
            else:
                monto = f.saldo_acreedor - f.saldo_deudor
                patrimonio_capital += monto
                item = ItemBalanceGeneral(codigo=cod, nombre=f.nombre, monto=monto)
                estructura[clase][subgrupo].append(item)

    # Determinar el resultado neto del ejercicio
    if tiene_resultado_asentado:
        res_final = resultado_ejercicio_asentado
    else:
        res_final = resumen_res.resultado_ejercicio
        if res_final != Decimal("0.00"):
            clase = "3. Capital / Patrimonio"
            subgrupo = "3.1 Capital Contable"
            nom_res = "Resultado del Ejercicio (Ganancia)" if res_final > 0 else "Resultado del Ejercicio (Pérdida)"
            item_res = ItemBalanceGeneral(
                codigo="3105",
                nombre=nom_res,
                monto=abs(res_final),
                es_regularizadora=(res_final < 0),
            )
            estructura[clase][subgrupo].append(item_res)

    total_activo = (total_act_corr + total_act_no_corr).quantize(TWO_PLACES)
    total_pasivo = (total_pas_corr + total_pas_no_corr).quantize(TWO_PLACES)
    total_patrimonio = (
        patrimonio_capital + patrimonio_reservas + patrimonio_resultados_acum + res_final
    ).quantize(TWO_PLACES)

    # Convertir estructura defaultdict a dict estándar
    estructura_dict = {c: dict(sg) for c, sg in estructura.items()}

    balance_gen = BalanceSituacionGeneral(
        empresa=empresa,
        periodo=periodo,
        fecha_emision=fecha_emision or date.today(),
        total_activo_corriente=total_act_corr.quantize(TWO_PLACES),
        total_activo_no_corriente=total_act_no_corr.quantize(TWO_PLACES),
        total_activo=total_activo,
        total_pasivo_corriente=total_pas_corr.quantize(TWO_PLACES),
        total_pasivo_no_corriente=total_pas_no_corr.quantize(TWO_PLACES),
        total_pasivo=total_pasivo,
        patrimonio_capital=patrimonio_capital.quantize(TWO_PLACES),
        patrimonio_reservas=patrimonio_reservas.quantize(TWO_PLACES),
        patrimonio_resultados_acumulados=patrimonio_resultados_acum.quantize(TWO_PLACES),
        resultado_ejercicio=res_final.quantize(TWO_PLACES),
        total_patrimonio=total_patrimonio,
        estructura=estructura_dict,
        resumen_resultados=resumen_res,
    )

    if validar_cuadre and not balance_gen.cuadra:
        raise EcuacionPatrimonialError(
            f"El Balance de Situación General no cumple con la Ecuación Patrimonial: "
            f"Total Activo ({balance_gen.total_activo}) != "
            f"Total Pasivo y Patrimonio ({balance_gen.total_pasivo_y_patrimonio}) "
            f"[Diferencia: {balance_gen.diferencia}]."
        )

    return balance_gen


class GestorBalance:
    """Controlador y servicio orquestador de Balances de Comprobación y Cierre."""

    def __init__(self, gestor_diario: Optional[Any] = None, gestor_mayor: Optional[Any] = None):
        self._gestor_diario = gestor_diario
        self._gestor_mayor = gestor_mayor
        self._balance_4c: Optional[Balance4Columnas] = None
        self._balance_general: Optional[BalanceSituacionGeneral] = None

    @property
    def gestor_mayor(self) -> GestorLibroMayor:
        if self._gestor_mayor is None:
            if self._gestor_diario is not None:
                self._gestor_mayor = GestorLibroMayor(self._gestor_diario.libro)
            else:
                self._gestor_mayor = GestorLibroMayor()
        return self._gestor_mayor

    def obtener_balance_4_columnas(self, sincronizar: bool = True) -> Balance4Columnas:
        """Obtiene o refresca la matriz de 4 Columnas a partir del estado actual del mayor."""
        if self._balance_4c is None or sincronizar:
            mayor = self.gestor_mayor.sincronizar()
            self._balance_4c = generar_balance_4_columnas(
                mayor,
                validar_cuadre=False,
                permitir_vacio=True,
            )
        return self._balance_4c

    def obtener_balance_general(self, sincronizar: bool = True) -> BalanceSituacionGeneral:
        """Obtiene o recalcula el Balance de Situación General de Cierre."""
        if self._balance_general is None or sincronizar:
            b4 = self.obtener_balance_4_columnas(sincronizar=sincronizar)
            self._balance_general = generar_balance_general(
                b4,
                validar_cuadre=False,
            )
        return self._balance_general
