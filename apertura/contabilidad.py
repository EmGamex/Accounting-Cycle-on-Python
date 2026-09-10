"""Lógica contable pura: consolidación de cuentas, cálculo de balance y partida de diario."""
from decimal import Decimal
from typing import Dict, List

from apertura.catalogo import normalizar
from apertura.models import (
    CuentaCatalogo,
    ItemCuentaApertura,
    LineaPartida,
    PartidaApertura,
    ResumenBalance,
)


class MotorApertura:
    """Motor contable sin efectos secundarios de entrada/salida para el proceso de apertura."""

    def __init__(self):
        self._items: Dict[str, ItemCuentaApertura] = {}

    @property
    def items(self) -> List[ItemCuentaApertura]:
        return list(self._items.values())

    def agregar_o_acumular(
        self,
        cuenta: CuentaCatalogo,
        monto: Decimal,
    ) -> ItemCuentaApertura:
        """Registra una cuenta en la apertura; si ya existe, acumula el monto."""
        clave = cuenta.codigo if cuenta.codigo != "S/C" else f"SC_{cuenta.nombre_norm}"

        if clave in self._items:
            item_existente = self._items[clave]
            nuevo_monto = (item_existente.monto + monto).quantize(Decimal("0.01"))
            self._items[clave] = ItemCuentaApertura(
                codigo=cuenta.codigo,
                nombre=cuenta.nombre,
                monto=nuevo_monto,
                clase=cuenta.clase,
                subgrupo=cuenta.subgrupo,
                es_regularizadora=cuenta.es_regularizadora,
            )
        else:
            self._items[clave] = ItemCuentaApertura(
                codigo=cuenta.codigo,
                nombre=cuenta.nombre,
                monto=monto.quantize(Decimal("0.01")),
                clase=cuenta.clase,
                subgrupo=cuenta.subgrupo,
                es_regularizadora=cuenta.es_regularizadora,
            )

        return self._items[clave]

    def eliminar(self, clave_o_codigo: str) -> bool:
        """Elimina una cuenta registrada por código o clave normalizada."""
        clave_limpia = clave_o_codigo.strip()
        if clave_limpia in self._items:
            del self._items[clave_limpia]
            return True

        # Búsqueda alternativa por nombre o normalizado
        norm = normalizar(clave_limpia)
        for k, v in list(self._items.items()):
            if normalizar(v.nombre) == norm or v.codigo == clave_limpia:
                del self._items[k]
                return True

        return False

    def vaciar(self) -> None:
        """Limpia todos los registros."""
        self._items.clear()

    def estructura_agrupada(self) -> Dict[str, Dict[str, Dict[str, ItemCuentaApertura]]]:
        """Organiza los items en {clase: {subgrupo: {clave: item}}}."""
        estructura: Dict[str, Dict[str, Dict[str, ItemCuentaApertura]]] = {}
        for item in self._items.values():
            clave = item.codigo if item.codigo != "S/C" else f"SC_{normalizar(item.nombre)}"
            grupo = estructura.setdefault(item.clase, {}).setdefault(item.subgrupo, {})
            grupo[clave] = item
        return estructura

    def calcular_balance(self) -> ResumenBalance:
        """Calcula los totales de Activo, Pasivo y Patrimonio respetando el efecto de cuentas regularizadoras."""
        t_activo = Decimal("0.00")
        t_pasivo = Decimal("0.00")
        t_patrimonio = Decimal("0.00")

        estructura = self.estructura_agrupada()

        for clase, subgrupos in estructura.items():
            cl_norm = normalizar(clase)
            subtotal_clase = Decimal("0.00")

            for _, cuentas in subgrupos.items():
                for cta in cuentas.values():
                    if cta.es_regularizadora:
                        subtotal_clase -= cta.monto
                    else:
                        subtotal_clase += cta.monto

            if "activo" in cl_norm:
                t_activo += subtotal_clase
            elif "pasivo" in cl_norm:
                t_pasivo += subtotal_clase
            elif any(k in cl_norm for k in ["capital", "patrimonio"]):
                t_patrimonio += subtotal_clase

        diferencia_capital = (t_activo - (t_pasivo + t_patrimonio)).quantize(Decimal("0.01"))

        return ResumenBalance(
            total_activo=t_activo.quantize(Decimal("0.01")),
            total_pasivo=t_pasivo.quantize(Decimal("0.01")),
            total_patrimonio=t_patrimonio.quantize(Decimal("0.01")),
            diferencia_capital=diferencia_capital,
            estructura_balance=estructura,
        )

    def asignar_diferencia_capital(self, cuenta_capital: CuentaCatalogo, monto: Decimal) -> ItemCuentaApertura:
        """Asigna la diferencia calculada directamente a la cuenta de capital."""
        return self.agregar_o_acumular(cuenta_capital, monto)

    def generar_partida_apertura(
        self,
        numero: int = 1,
        descripcion: str = "Registro de valores iniciales al inicio de operaciones.",
    ) -> PartidaApertura:
        """Genera el asiento contable de apertura clasificando débitos y créditos con rigor técnico."""
        debe_filas: List[LineaPartida] = []
        haber_filas: List[LineaPartida] = []

        estructura = self.estructura_agrupada()

        for clase, subgrupos in estructura.items():
            cl_norm = normalizar(clase)
            for _, cuentas in subgrupos.items():
                for cta in cuentas.values():
                    if "activo" in cl_norm:
                        if cta.es_regularizadora:
                            # Ejemplo: Depreciación Acumulada va al Haber
                            haber_filas.append(LineaPartida(codigo=cta.codigo, nombre=cta.nombre, haber=cta.monto))
                        else:
                            debe_filas.append(LineaPartida(codigo=cta.codigo, nombre=cta.nombre, debe=cta.monto))
                    else:
                        # Pasivo o Capital
                        if cta.es_regularizadora:
                            # Ejemplo: Pérdidas Acumuladas va al Debe
                            debe_filas.append(LineaPartida(codigo=cta.codigo, nombre=cta.nombre, debe=cta.monto))
                        else:
                            haber_filas.append(LineaPartida(codigo=cta.codigo, nombre=cta.nombre, haber=cta.monto))

        lineas = debe_filas + haber_filas
        total_debe = sum((l.debe for l in lineas), Decimal("0.00")).quantize(Decimal("0.01"))
        total_haber = sum((l.haber for l in lineas), Decimal("0.00")).quantize(Decimal("0.01"))

        return PartidaApertura(
            numero=numero,
            descripcion=descripcion,
            lineas=lineas,
            total_debe=total_debe,
            total_haber=total_haber,
        )
