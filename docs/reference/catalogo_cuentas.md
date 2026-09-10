# Referencia: Catálogo de Cuentas NIIF / SAT

Este documento contiene la nomenclatura formal completa utilizada por el sistema, compatible con NIIF para PYMES y la legislación mercantil y tributaria de Guatemala.

---

## 1. Activo (Naturaleza Deudora)

### 1.1 Activo Corriente
| Código | Nombre de la Cuenta | Naturaleza | Tipo / Notas |
| :--- | :--- | :---: | :--- |
| `1101` | Caja General | Deudora | Disponible líquido |
| `1102` | Bancos (Moneda Nacional) | Deudora | Cuentas monetarias y de ahorro |
| `1103` | Cuentas por Cobrar Clientes | Deudora | Exigible comercial |
| `1103-R` | (-) Estimación para Cuentas Incobrables | **Acreedora** | **Regularizadora de Activo** |
| `1104` | Inventario de Mercancías | Deudora | Realizable comercial |
| `1105` | Material de Empaque | Deudora | Realizable operativo |
| `1106` | Moneda Extranjera | Deudora | Divisas extranjeras |
| `1107` | Crédito Fiscal | Deudora | IVA soportado en compras (12%) |
| `1108` | Combustibles y Lubricantes | Deudora | Existencias de consumo |
| `1109` | Caja Chica | Deudora | Fondo fijo administrativo |
| `1110` | Anticipos a Proveedores | Deudora | Pagos a cuenta de bienes/servicios |
| `1111` | Anticipos sobre Sueldos a Empleados | Deudora | Crédito a favor de la empresa |
| `1112` | Alquileres Pagados por Anticipado | Deudora | Gasto diferido |
| `1113` | Seguros Pagados por Anticipado | Deudora | Gasto diferido |

### 1.2 Activo No Corriente
| Código | Nombre de la Cuenta | Naturaleza | Tipo / Notas |
| :--- | :--- | :---: | :--- |
| `1201` | Terrenos | Deudora | Inmueble no sujeto a depreciación |
| `1202` | Edificios | Deudora | Tasa legal de depreciación: 5% |
| `1203` | Maquinaria y Equipo | Deudora | Tasa legal de depreciación: 20% |
| `1204` | Mobiliario y Equipo de Oficina | Deudora | Tasa legal de depreciación: 20% |
| `1205` | (-) Depreciación Acumulada | **Acreedora** | **Regularizadora global** |
| `1205-01` | (-) Depreciación Acumulada Edificios | **Acreedora** | Regularizadora específica |
| `1205-02` | (-) Depreciación Acumulada Maquinaria | **Acreedora** | Regularizadora específica |
| `1205-03` | (-) Depreciación Acumulada Mobiliario y Equipo | **Acreedora** | Regularizadora específica |
| `1205-04` | (-) Depreciación Acumulada Vehículos | **Acreedora** | Regularizadora específica |
| `1206` | Vehículos | Deudora | Tasa legal de depreciación: 20% |
| `1207` | Documentos por Cobrar a Largo Plazo | Deudora | Exigible a más de 1 año |
| `1208` | Herramientas | Deudora | Tasa legal de depreciación: 25% |
| `1209` | Marcas y Patentes | Deudora | Activo intangible |
| `1210` | (-) Amortización Acumulada | **Acreedora** | **Regularizadora de intangible** |

---

## 2. Pasivo (Naturaleza Acreedora)

### 2.1 Pasivo Corriente
| Código | Nombre de la Cuenta | Naturaleza | Tipo / Notas |
| :--- | :--- | :---: | :--- |
| `2101` | Proveedores Locales | Acreedora | Deudas comerciales a corto plazo |
| `2102` | Cuentas por Pagar a Corto Plazo | Acreedora | Obligaciones diversas |
| `2103` | Impuestos por Pagar | Acreedora | Tributos fiscales retenidos o directos |
| `2104` | Sueldos y Salarios Retenidos | Acreedora | Agrupador de nómina |
| `2104-01` | Cuotas IGSS por Pagar (Laboral + Patronal) | Acreedora | 4.83% laboral + 12.67% patronal (17.50%) |
| `2104-02` | Retención ISR Sueldos por Pagar | Acreedora | ISR Decreto 10-2012 |
| `2104-03` | Retención ISR Compras y Servicios por Pagar | Acreedora | ISR retenciones 5%/12% |
| `2104-04` | Sueldos y Salarios por Pagar | Acreedora | Líquido de planilla pendiente de cobro |
| `2104-05` | Otras Retenciones por Pagar | Acreedora | Descuentos judiciales, cooperativas |
| `2105` | IVA por Pagar | Acreedora | Débito fiscal generado en ventas (12%) |
| `2106` | Acreedores | Acreedora | Acreedores no comerciales |
| `2107` | Intereses por Pagar | Acreedora | Cargas financieras devengadas |
| `2108` | Provisiones para Prestaciones Laborales | Acreedora | Aguinaldo, Bono 14, Vacaciones |

### 2.2 Pasivo No Corriente
| Código | Nombre de la Cuenta | Naturaleza | Tipo / Notas |
| :--- | :--- | :---: | :--- |
| `2201` | Acreedores Hipotecarios | Acreedora | Garantía sobre inmuebles |
| `2202` | Préstamos Bancarios a Largo Plazo | Acreedora | Deudas financieras > 1 año |
| `2203` | Documentos por Pagar a Largo Plazo | Acreedora | Pagarés comerciales |
| `2204` | Hipotecas | Acreedora | Gravámenes a largo plazo |
| `2205` | Reserva para Indemnizaciones Laborales | Acreedora | Pasivo contingente laboral |

---

## 3. Capital / Patrimonio (Naturaleza Acreedora)

| Código | Nombre de la Cuenta | Naturaleza | Notas |
| :--- | :--- | :---: | :--- |
| `3101` | Capital Social | Acreedora | Aportaciones de socios o dueño individual |
| `3102` | Reserva Legal | Acreedora | 5% sobre utilidades netas (Art. 86 C.Comercio) |
| `3103` | Utilidades Acumuladas de Ejercicios Anteriores | Acreedora | Beneficios no distribuidos |
| `3104` | (-) Pérdidas Acumuladas | **Deudora** | **Regularizadora de Patrimonio** |
| `3105` | Resultado del Ejercicio | Deudora/Acreedora | Utilidad o pérdida neta del período |

---

## 4. Ingresos (Naturaleza Acreedora)

| Código | Nombre de la Cuenta | Naturaleza | Notas |
| :--- | :--- | :---: | :--- |
| `4101` | Ventas de Mercancías | Acreedora | Ingreso principal sin IVA |
| `4102` | Prestación de Servicios | Acreedora | Honorarios o servicios prestados |
| `4103` | (-) Devoluciones y Rebajas sobre Ventas | **Deudora** | **Regularizadora de Ingresos** |
| `4201` | Otros Ingresos | Acreedora | Ingresos no operacionales |
| `4202` | Productos Financieros (Intereses Ganados) | Acreedora | Rentas de capital |
| `4203` | Diferenciales Cambiarios | Acreedora | Ganancia cambiaria realizada |

---

## 5. Costos y Gastos (Naturaleza Deudora)

| Código | Nombre de la Cuenta | Naturaleza | Notas |
| :--- | :--- | :---: | :--- |
| `5101` | Costo de Ventas | Deudora | Inventario inicial + compras netas - inventario final |
| `5102` | Compras de Materia Prima / Mercadería | Deudora | Compras brutas del período sin IVA |
| `5103` | Gastos sobre Compras | Deudora | Fletes, acarreos y seguros de importación |
| `5201-01` | Sueldos de Administración | Deudora | Salarios base + extraordinarios admin |
| `5201-02` | Bonificación Incentivo Administración | Deudora | Q250.00 fijos por empleado |
| `5201-03` | Cuota Patronal Administración | Deudora | 12.67% sobre devengado afecto |
| `5202-01` | Sueldos Sala de Ventas | Deudora | Salarios base + extraordinarios ventas |
| `5202-02` | Comisiones sobre Ventas | Deudora | Comisiones devengadas |
| `5202-03` | Bonificación Incentivo Ventas | Deudora | Q250.00 fijos por vendedor |
| `5202-04` | Cuota Patronal Ventas | Deudora | 12.67% sobre devengado afecto |
| `5203` | Gastos Generales (Agua, Luz, Teléfono, Alquileres) | Deudora | Servicios básicos devengados |
