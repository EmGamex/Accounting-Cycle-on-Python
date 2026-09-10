# Referencia: Legislación y Parámetros Fiscales de Guatemala

Este documento compila el marco normativo, leyes de la República de Guatemala, decretos del Congreso y acuerdos gubernativos/institucionales que rigen los cálculos y libros contables de este software.

---

## 1. Código de Comercio de Guatemala (Decreto 2-70)

### Obligación de Llevar Contabilidad Completa
* **Artículo 368 (Contabilidad y Registros Indispensables):**
  Los comerciantes están obligados a llevar su contabilidad en forma organizada, de acuerdo con el sistema de partida doble y usando principios de contabilidad generalmente aceptados (o NIIF).
  Deben llevar como mínimo los siguientes libros principales:
  1. Inventarios
  2. Diario (de primera entrada)
  3. Mayor o Centralizador
  4. Estados Financieros (Balances)
* **Artículo 369 (Idioma y Moneda):**
  Los libros y registros deben operarse en idioma español y en moneda nacional (Quetzales, `Q`).
* **Artículo 371 (Forma de Operar):**
  Prohíbe alterar el orden o fecha de las operaciones, dejar espacios en blanco, hacer raspaduras o enmiendas. Todo error debe corregirse mediante un asiento de contrapartida o ajuste en el Libro Diario.
* **Artículo 373 (Libro Diario):**
  En el libro diario se asentará día por día y por el orden en que se vayan efectuando todas las operaciones que haga el comerciante, expresando detalladamente el carácter y circunstancias de cada una de ellas.

---

## 2. Régimen de Seguridad Social (IGSS)

Base legal: Ley Orgánica del Instituto Guatemalteco de Seguridad Social (Decreto 295) y Acuerdo 1118 de Junta Directiva (Reglamento sobre Recaudación de Contribuciones).

### Cuotas Vigentes:
* **Cuota Laboral (Deducción al Trabajador):**
  $$\text{IGSS Laboral} = 4.83\% \times \text{Total Devengado Afecto}$$
  * Afecto: Sueldo base, comisiones, horas extras, propinas.
  * No afecto: Bonificación incentivo (Decreto 78-89), viáticos comprobables.
* **Cuota Patronal (Carga a la Empresa):**
  $$\text{IGSS Patronal} = 12.67\% \times \text{Total Devengado Afecto}$$
  * Desglose:
    * **10.67%**: Instituto Guatemalteco de Seguridad Social (IGSS - IVS / EMA).
    * **1.00%**: Instituto de Recreación de los Trabajadores de la Empresa Privada de Guatemala (IRTRA - Decreto 1528).
    * **1.00%**: Instituto Técnico de Capacitación y Productividad (INTECAP - Decreto 17-72).
* **Total Cuotas a Pagar al IGSS en Planilla Única:**
  $$\text{Total Aportación} = 4.83\% + 12.67\% = 17.50\%$$

---

## 3. Bonificación Incentivo (Decreto 78-89 y 37-2001)

* **Monto:** **Q 250.00 mensuales** mínimos por trabajador para el sector privado.
* **Naturaleza:** Es un incentivo no afecto al pago de cuotas del IGSS, ni para el cálculo de indemnización, aguinaldo o bono 14.
* **Cálculo Proporcional:** Si el empleado no laboró el mes completo, se liquida proporcionalmente a los días efectivamente trabajados ($Q 250.00 / 30 \times \text{días}$).

---

## 4. Impuesto Sobre la Renta (ISR) — Asalariados (Decreto 10-2012)

Base legal: Ley de Actualización Tributaria (Libro I, Rentas del Trabajo).

### Determinación de la Renta Imponible Anual:
$$\text{Renta Bruta Proyectada} = (\text{Sueldo Base} + \text{Comisiones Estimadas} + \text{Horas Extras}) \times 12 + \text{Bono 14} + \text{Aguinaldo}$$

### Deducciones de Ley Permitidas:
1. Deducción personal sin necesidad de comprobación: **Q 48,000.00** anuales.
2. Cuota de IGSS laboral anual proyectada ($4.83\%$).
3. Aguinaldo y Bono 14 exentos hasta el 100% del sueldo ordinario mensual promedio.

### Escala de Tasas Impositivas:
| Renta Imponible Neta Anual | Tasa Impositiva | Importe Fijo |
| :--- | :---: | :---: |
| De Q 0.01 a Q 300,000.00 | **5%** | Q 0.00 |
| Sobre el excedente de Q 300,000.00 | **7%** | Q 15,000.00 |

* **Retención Mensual:** El impuesto anual proyectado se divide entre los meses que resten del período fiscal.

---

## 5. Impuesto al Valor Agregado (IVA - Decreto 27-92)

* **Tasa General:** **12%** incluido en todos los precios de venta al consumidor.
* **Desglose en Compras / Servicios Recibidos (Crédito Fiscal):**
  $$\text{Precio sin IVA (Base)} = \frac{\text{Total Factura}}{1.12}$$
  $$\text{Crédito Fiscal (Cuenta 1107)} = \text{Base} \times 0.12$$
* **Desglose en Ventas / Servicios Prestados (Débito Fiscal):**
  $$\text{Venta Neta (Cuenta 4101)} = \frac{\text{Total Factura}}{1.12}$$
  $$\text{Débito Fiscal (Cuenta 2105)} = \text{Venta Neta} \times 0.12$$
