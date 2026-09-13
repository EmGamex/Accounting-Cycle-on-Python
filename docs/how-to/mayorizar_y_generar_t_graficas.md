# Guía Práctica: Cómo Mayorizar Cuentas y Generar T-Gráficas

Esta guía paso a paso explica cómo operar el subsistema de Libro Mayor (`mayor/`), realizar la mayorización automática de las partidas asentadas en el Libro Diario, interpretar las vistas en T-Gráficas y formato a 3 columnas, y detectar posibles saldos anómalos.

---

## 1. Acceso al Módulo de Mayor

El flujo de mayorización se encuentra integrado en el orquestador general:

1. Inicia el sistema:
   ```bash
   python main.py
   ```
2. En el menú principal, selecciona la opción:
   `[4] Sistema de Libro Mayor y T-Gráficas (Pases y Saldos)`

Al ingresar, el sistema sincroniza automáticamente todas las partidas del Libro Diario y despliega el resumen del Mayor:
```text
Libro Mayor Actual: 12 cuenta(s) activa(s) | Debe: Q 158,500.00 | Haber: Q 158,500.00 [CUADRA]
```

---

## 2. Visualización de T-Gráficas Didácticas

Para auditar visualmente los débitos y créditos agrupados por cuenta:

1. Selecciona la opción **`[1] Ver T-Gráficas en pantalla`**.
2. El sistema renderizará para cada cuenta una tabla con estilo de Cuenta T:
   * **Columna Izquierda (Debe):** Lista de cargos con número de partida de origen, fecha y monto.
   * **Columna Derecha (Haber):** Lista de abonos con número de partida de origen, fecha y monto.
   * **Pie de Cuenta:** Total Debe, Total Haber y el **Saldo de Cierre** (Deudor o Acreedor).

```text
               ┌────────────────────── 1102 - Bancos ──────────────────────┐
               │ DEBE (Cargos)             │ HABER (Abonos)                │
               ├───────────────────────────┼───────────────────────────────┤
               │ P#1 01/01/2026 Q 50,000.00│ P#2 31/01/2026 Q  9,454.61    │
               ├───────────────────────────┼───────────────────────────────┤
               │ TOTAL DEBE:    Q 50,000.00│ TOTAL HABER:   Q  9,454.61    │
               ├───────────────────────────┴───────────────────────────────┤
               │ SALDO DEUDOR: Q 40,545.39                                 │
               └───────────────────────────────────────────────────────────┘
```

---

## 3. Inspección del Mayor Formal a 3 Columnas

Para emitir el libro comercial continuo conforme al Código de Comercio de Guatemala:

1. Selecciona la opción **`[2] Ver Libro Mayor formal (3 columnas)`**.
2. Esta vista presenta un registro cronológico por cada movimiento con su saldo continuo resultante:
   * **Fecha:** Día de la operación.
   * **P#:** Número correlativo de partida en el Diario.
   * **Concepto:** Descripción del movimiento.
   * **Debe / Haber:** Importe imputado.
   * **Saldo:** Valor acumulado en tiempo real respetando la naturaleza acreedora o deudora de la cuenta.

---

## 4. Detección de Saldos Anómalos

El motor ([`mayor.models.CuentaMayor`](../../mayor/models.py)) evalúa automáticamente si el saldo resultante contradice la naturaleza de la cuenta:

* **Cuentas de Activo (1) o Gasto (5):** Se espera saldo **DEUDOR**.
* **Cuentas de Pasivo (2), Patrimonio (3) o Ingreso (4):** Se espera saldo **ACREEDOR**.
* **Cuentas Regularizadoras (-R, 1205, 1210):** Se espera saldo **ACREEDOR**.

Si una cuenta presenta un saldo opuesto (por ejemplo, Caja con saldo acreedor por sobregiro físico imposible):
1. El sistema marcará la cuenta con la advertencia `[SALDO ANÓMALO]`.
2. Debes revisar en el Libro Diario las partidas que afectaron dicha cuenta para corregir errores de digitación o invertir cargos/abonos.

---

## 5. Exportación a Disco

Para conservar copias físicas auditables de las cuentas mayorizadas:

* Opción **`[3] Exportar T-Gráficas a archivo de texto`**: Genera el archivo `t_graficas_mayor.txt`.
* Opción **`[4] Exportar Libro Mayor formal a archivo de texto`**: Genera el archivo `libro_mayor_formal.txt`.

Ambos archivos se guardan en codificación UTF-8 en la raíz del proyecto.
