# Guía Práctica: Cómo Estructurar Partidas en el Libro Diario

Esta guía explica las normas formales, técnicas y legales para asentar partidas en el Libro Diario a 2 columnas conforme al Código de Comercio de Guatemala (Art. 368 al 373) y el modelo de datos unificado del sistema.

---

## 1. Anatomía de una Partida Contable Formal

Toda partida en el Libro Diario debe contener los siguientes 5 elementos obligatorios:

```text
Partida No. X ------------------------------------------- [Fecha: DD/MM/AAAA]
Código    Cuenta / Explicación                                Debe        Haber
-------------------------------------------------------------------------------
[CÓDIGO]  Cuenta Deudora (Cargada)                        Q XXX.XX
[CÓDIGO]  Cuenta Deudora (Cargada)                        Q YYY.YY
[CÓDIGO]     A: Cuenta Acreedora (Abonada con sangría)                Q ZZZ.ZZ
[CÓDIGO]     A: Cuenta Acreedora (Abonada con sangría)                Q WWW.WW
          Glosa o Explicación circunstanciada de la operación.
-------------------------------------------------------------------------------
SUMAS IGUALES:                                            Q TTT.TT    Q TTT.TT
===============================================================================
```

### Reglas de Estilo y Nomenclatura:
1. **Cuentas Deudoras (Debe):** Se escriben alineadas al margen izquierdo sin prefijos.
2. **Cuentas Acreedoras (Haber):** Llevan una sangría visual hacia la derecha (convencionalmente 3 a 5 espacios) y se les antecede opcionalmente la preposición *"A:"* o *"a:"*.
3. **Glosa (Sinopsis):** Texto claro que describe el hecho económico e identifica los comprobantes de respaldo (facturas serie y número, cheques, pólizas de importación, etc.).
4. **Sumas Iguales:** Línea de cierre al pie de cada asiento donde la suma de débitos coincide exactamente con la suma de créditos.

---

## 2. Ejemplos de Asientos Comunes en Guatemala

### Ejemplo 1: Compra de Mercaderías al Contado con Factura
* Base de cálculo: En Guatemala el IVA (12%) está incluido en el precio de factura.
  * Factura total: Q 11,200.00
  * Base de compra: $11,200 / 1.12 = \text{Q } 10,000.00$
  * Crédito Fiscal IVA: $10,000 \times 0.12 = \text{Q } 1,200.00$

```text
Partida No. 2 ------------------------------------------- [Fecha: 05/01/2026]
1104      Inventario de Mercancías (o Compras)         Q 10,000.00
1107      Crédito Fiscal                                Q  1,200.00
1102         A: Bancos (Moneda Nacional)                              Q 11,200.00
          Por compra de mercadería al contado según factura No. 45892 de 
          Distribuidora Central, pagada con cheque No. 101 de Banco Industrial.
-------------------------------------------------------------------------------
SUMAS IGUALES:                                         Q 11,200.00    Q 11,200.00
```

### Ejemplo 2: Venta de Mercaderías al Crédito
* Factura total: Q 22,400.00
  * Base de venta: $22,400 / 1.12 = \text{Q } 20,000.00$
  * Débito Fiscal IVA: $20,000 \times 0.12 = \text{Q } 2,400.00$

```text
Partida No. 3 ------------------------------------------- [Fecha: 12/01/2026]
1103      Cuentas por Cobrar Clientes                  Q 22,400.00
4101         A: Ventas de Mercancías                                  Q 20,000.00
2105         A: IVA por Pagar (Débito Fiscal)                         Q  2,400.00
          Por venta de mercaderías al crédito a 30 días según factura FEL 
          electrónica No. 89123 a favor de Comercial El Éxito.
-------------------------------------------------------------------------------
SUMAS IGUALES:                                         Q 22,400.00    Q 22,400.00
```

---

## 3. Modelo de Datos en Python (`PartidaDiario`)

Para asegurar la robustez de los asientos dentro del código, se utiliza la siguiente estructura tipada:

```python
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List

@dataclass
class MovimientoLinea:
    codigo: str
    nombre: str
    debe: Decimal = Decimal("0.00")
    haber: Decimal = Decimal("0.00")

@dataclass
class PartidaDiario:
    numero: int
    fecha: date
    glosa: str
    lineas: List[MovimientoLinea] = field(default_factory=list)
    origen: str = "MANUAL"  # "APERTURA", "PLANILLA", "VENTA", "COMPRA"

    @property
    def total_debe(self) -> Decimal:
        return sum((l.debe for l in self.lineas), Decimal("0.00"))

    @property
    def total_haber(self) -> Decimal:
        return sum((l.haber for l in self.lineas), Decimal("0.00"))

    @property
    def cuadra(self) -> bool:
        return self.total_debe == self.total_haber
```

---

## 4. Control de Errores Comunes
* **Error de centavo por redondeo:** Ocurre si se divide entre 1.12 usando `float`. Solución: Usar `Decimal('1.12')` y cuantificar el residuo con `quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)`.
* **Cuentas invertidas:** Cargar una cuenta de pasivo cuando debió abonarse. El catálogo define la naturaleza de cada cuenta para advertir al operador si un saldo resulta anómalo.
