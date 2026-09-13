# Explicación: El Ciclo Contable y el Efecto Dominó hacia el Mayor y Balance

Este artículo explica la justificación teórica y matemática de por qué la captura rigurosa en el Libro Diario permite automatizar en un 100% el Libro Mayor (T-Gráficas), el Balance de 4 Columnas y los Estados Financieros finales sin intervención manual adicional.

---

## 1. El Fundamento Matemático de la Partida Doble

La contabilidad por partida doble, formulada originalmente por Fray Luca Pacioli en 1494 y adoptada universalmente, establece que **no hay deudor sin acreedor, ni acreedor sin deudor**.

En términos algebraicos, toda transacción contable $k$ es un vector bidimensional de cargos $D_k$ y abonos $H_k$ tal que:

$$\sum_{i} d_{k, i} = \sum_{j} h_{k, j}$$

Donde $d_{k, i}$ es el monto cargado a la cuenta $i$ y $h_{k, j}$ es el monto abonado a la cuenta $j$.

Por consiguiente, si cada partida individual $k$ cumple con la condición de igualdad estricta, la sumatoria acumulada de todas las partidas del ejercicio contable también debe cumplirla necesariamente:

$$\sum_{k=1}^{N} \sum_{i} d_{k, i} = \sum_{k=1}^{N} \sum_{j} h_{k, j}$$

Esta propiedad transitiva es la que garantiza que los libros derivados cuadren de forma infalible.

---

## 2. La Transformación: De Libro Diario a Libro Mayor

El **Libro Diario** es una secuencia ordenada temporalmente:
$$\text{Diario} = [P_1, P_2, P_3, \dots, P_N]$$

Cada partida contiene líneas que apuntan a diversas cuentas catalogadas. Por ejemplo:
* $P_1$: `1.01.01.01 Caja General` (+Q10,000), `3.01.01.01 Capital Social` (-Q10,000)
* $P_2$: `1.01.01.02 Bancos del Sistema` (+Q8,000), `1.01.01.01 Caja General` (-Q8,000)
* $P_3$: `5.01.01.01 Sueldos de Administración` (+Q5,000), `1.01.01.02 Bancos del Sistema` (-Q5,000)

### ¿Qué es el Libro Mayor en términos computacionales?
El Libro Mayor no es más que una operación de **agrupamiento por clave** (`GROUP BY codigo_cuenta`):

```mermaid
flowchart LR
    subgraph DiarioInput ["ENTRADA: Asientos del Libro Diario"]
        L1["P#1: 1.01.01.01 Caja General (Debe Q10,000)"]
        L2["P#2: 1.01.01.01 Caja General (Haber Q8,000)"]
        L3["P#2: 1.01.01.02 Bancos (Debe Q8,000)"]
        L4["P#3: 5.01.01.01 Sueldos Admin (Debe Q5,000)"]
    end

    subgraph Transformacion ["TRANSFORMACIÓN COMPUTACIONAL"]
        GB["Agrupamiento por Código NIIF<br/><b>group_by(codigo_cuenta)</b>"]
    end

    subgraph MayorOutput ["SALIDA: T-Gráficas del Libro Mayor"]
        T1["<b>1.01.01.01 Caja General</b><br/>Debe: Q10,000 │ Haber: Q8,000<br/>───<br/><b>Saldo Deudor: Q 2,000.00</b>"]
        T2["<b>1.01.01.02 Bancos</b><br/>Debe: Q 8,000 │ Haber: Q 5,000<br/>───<br/><b>Saldo Deudor: Q 3,000.00</b>"]
    end

    L1 & L2 --> GB --> T1
    L3 --> GB --> T2
```

Dado que el agrupamiento no altera las magnitudes numéricas, la suma de todos los débitos en el Mayor es idéntica a la suma de todos los débitos en el Diario.

---

## 3. La Construcción del Balance de 4 Columnas

El **Balance de Comprobación y Saldos (4 Columnas)** toma directamente los resultados de cada cuenta calculada en [`mayor/engine.py`](../../mayor/engine.py):

1. **Columna 1 (Suma Debe):** $\sum Debe$ de la cuenta.
2. **Columna 2 (Suma Haber):** $\sum Haber$ de la cuenta.
3. **Columna 3 (Saldo Deudor):** Si $\sum Debe > \sum Haber \implies \text{Saldo} = \sum Debe - \sum Haber$.
4. **Columna 4 (Saldo Acreedor):** Si $\sum Haber > \sum Debe \implies \text{Saldo} = \sum Haber - \sum Debe$.

### Demostración del Doble Cuadre:
* Las **Sumas** cuadran porque representan exactamente el total de cargos y abonos del Diario redistribuidos por cuenta:
  $$\sum \text{Columna 1} = \sum \text{Columna 2}$$
* Los **Saldos** cuadran porque la resta de cantidades iguales a ambos lados de una ecuación mantiene la igualdad:
  $$\sum \text{Columna 3 (Saldos Deudores)} = \sum \text{Columna 4 (Saldos Acreedores)}$$

---

## 4. Conclusión y Valor de la Automatización

En la contabilidad tradicional en papel, los errores de pase (trasladar cifras incorrectas del Diario al Mayor o sumar erróneamente columnas extensas) consumen incontables horas de búsqueda y conciliación.

Al implementar este flujo en Python con [`diario.engine.GestorLibroDiario`](../../diario/engine.py) y [`mayor.engine`](../../mayor/engine.py):
1. Los módulos operativos solo se concentran en validar los hechos económicos de origen (apertura, compras, ventas, nóminas).
2. El sistema aplica la regla de bloqueo preventivo: **ninguna partida con descuadre puede ser grabada**.
3. El Libro Mayor, las T-Gráficas y el Balance de 4 Columnas se derivan en milisegundos con exactitud matemática absoluta.
