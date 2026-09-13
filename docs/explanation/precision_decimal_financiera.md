# Explicación: Precisión Financiera con Decimal vs Float

Este artículo detalla la justificación técnica por la cual este sistema prohíbe el uso de tipos de punto flotante nativos (`float`) en Python para operaciones monetarias, y adopta de manera estricta la biblioteca estándar `decimal.Decimal`.

---

## 1. El Problema del Punto Flotante Binario (IEEE 754)

Las computadoras utilizan internamente el sistema binario (base 2). En la especificación IEEE 754, la mayoría de las fracciones decimales familiares en el comercio (como $0.10$, $0.20$ o $0.05$) no pueden representarse de forma exacta como potencias de dos, generando expansiones infinitas periódicas:

$$0.1_{10} = 0.000110011001100110011..._2$$

Cuando Python evalúa una suma aparentemente trivial en `float`:

```python
>>> 0.1 + 0.2
0.30000000000000004
>>> (0.1 + 0.2) == 0.3
False
```

### El Impacto Fatal en la Contabilidad
En contabilidad formal y fiscal:
1. Una partida **debe cuadrar exactamente al centavo**: `total_debe == total_haber`. Si la diferencia es `0.00000000000000004`, una comparación estricta de igualdad fallará y el software reportará un falso descuadre.
2. Al acumular miles de transacciones a lo largo de un ejercicio anual, los errores por redondeo en coma flotante se propagan y terminan alterando los centavos de balances oficiales, provocando reparos o multas de auditoría tributaria ante la SAT.

---

## 2. La Solución: Aritmética de Base 10 con `Decimal`

La biblioteca `decimal` de Python implementa el estándar formal **IBM General Decimal Arithmetic Specification**. En lugar de aproximar en binario, almacena los números como coeficientes enteros y exponentes en base 10:

```python
from decimal import Decimal

>>> Decimal("0.1") + Decimal("0.2")
Decimal('0.3')

>>> (Decimal("0.1") + Decimal("0.2")) == Decimal("0.3")
True
```

### Reglas de Implementación en el Código
Para asegurar la pureza del cálculo en todo el sistema:

1. **Inicialización Obligatoria como Cadena (`str`):**
   * **Incorrecto:** `Decimal(0.1)` — ya introduce el error de precisión del float antes de construir el objeto.
   * **Correcto:** `Decimal("0.1")` o `Decimal("1500.50")`.

2. **Redondeo Legal con `ROUND_HALF_UP` y Constantes Centralizadas:**
   En Guatemala, los centavos se redondean al entero más próximo, y las fracciones exactamente iguales a $0.5$ se redondean hacia arriba (redondeo escolar / bancario comercial). En el sistema, esto se apoya en las constantes de [`config.py`](../../config.py):
   ```python
   from decimal import Decimal, ROUND_HALF_UP
   from config import PRECISION_CENTAVOS, CERO_MONETARIO

   # PRECISION_CENTAVOS = Decimal("0.01")
   # CERO_MONETARIO = Decimal("0.00")

   def redondear_moneda(valor: Decimal) -> Decimal:
       return valor.quantize(PRECISION_CENTAVOS, rounding=ROUND_HALF_UP)
   ```

3. **Cálculo de Porcentajes:**
   Al calcular retenciones e impuestos (como el IGSS laboral $4.83\%$), se utilizan las constantes configuradas:
   ```python
   from config import TASA_IGSS_LABORAL  # Decimal("0.0483")

   cuota_igss = (total_afecto * TASA_IGSS_LABORAL).quantize(
       PRECISION_CENTAVOS, rounding=ROUND_HALF_UP
   )
   ```
   Garantizando que el resultado sea siempre un múltiplo exacto de `0.01` Quetzales.

---

## 3. Comparativa de Rendimiento vs Fiabilidad

| Aspecto | `float` nativo | `decimal.Decimal` |
| :--- | :---: | :---: |
| **Exactitud Monetaria** | Deficiente (aproximación binaria) | **100% exacta al centavo** |
| **Cumplimiento Tributario (SAT)** | No apto | **Totalmente auditable** |
| **Velocidad de CPU** | Nanosegundos (soporte por hardware) | Microsegundos (software) |
| **Consumo de Memoria** | Muy bajo | Bajo |

En sistemas contables y financieros, procesar 100,000 transacciones en 0.2 segundos con `Decimal` frente a 0.01 segundos con `float` es una diferencia imperceptible para el usuario, pero la diferencia entre un balance auditado exitosamente y un balance con centavos descuadrados es absoluta.
