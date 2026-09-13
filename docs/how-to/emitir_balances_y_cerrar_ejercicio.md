# Guía Práctica: Cómo Emitir Balances y Gestionar el Cierre del Ejercicio

Esta guía paso a paso explica cómo utilizar el subsistema de Balances (`balance/`) y Persistencia (`persistencia/`) para emitir el Balance de Comprobación y Saldos (4 Columnas), generar el Balance de Situación General de Cierre y guardar o respaldar el ejercicio contable.

---

## 1. Emisión del Balance de Comprobación y Saldos (4 Columnas)

El Balance de 4 Columnas verifica la integridad aritmética de todas las operaciones del período contable:

1. Inicia el sistema con `python main.py`.
2. Selecciona la opción **`[5] Sistema de Balances (4 Columnas y Situación General de Cierre)`**.
3. Elige **`[1] Generar y ver Balance de 4 Columnas`**.

### Verificación del Doble Cuadre
La tabla muestra cada cuenta activa del catálogo con sus importes:
* **Columna 1 y 2 (Sumas Debe y Haber):** Comprueba que la redistribución de partidas sume exactamente igual ($\sum \text{Debe} == \sum \text{Haber}$).
* **Columna 3 y 4 (Saldos Deudor y Acreedor):** Comprueba que la diferencia neta de cuentas mantenga la igualdad patrimonial ($\sum \text{Saldos Deudores} == \sum \text{Saldos Acreedores}$).

Al pie de la tabla, confirma el indicador:
`[bold green][CUADRADO PERFECTAMENTE][/bold green]`

Para archivar el balance oficial, selecciona **`[2] Exportar Balance a archivo de texto`** (guardará `balance_4_columnas.txt`).

---

## 2. Generación del Balance de Situación General de Cierre

Para obtener el estado financiero formal clasificado al cierre del ejercicio contable:

1. Dentro del menú de Balances, selecciona la opción **`[3] Ver Balance de Situación General de Cierre`**.
2. El sistema filtrará únicamente las cuentas reales (Clases 1, 2 y 3) y calculará la estructura canónica:
   * **Activo Corriente** (Caja, Bancos, Inventarios, Crédito Fiscal).
   * **Activo No Corriente** (Bienes duraderos menos cuentas regularizadoras de depreciación y amortización acumuladas).
   * **Pasivo Corriente y No Corriente**.
   * **Patrimonio Neto** (Capital Social, Reservas y Resultado del Ejercicio).
3. Verifica la ecuación patrimonial de cierre:
   $$\text{Total Activo} = \text{Total Pasivo} + \text{Total Patrimonio}$$

Para exportar este estado financiero, selecciona **`[4] Exportar Balance General a archivo de texto`** (generará `balance_situacion_general.txt`).

---

## 3. Persistencia y Gestión del Ejercicio Contable (`persistencia/`)

Para asegurar la continuidad del negocio y reanudar operaciones en sesiones posteriores:

### Guardado del Ejercicio
Desde el menú principal:
* Selecciona **`[6] Guardar / Cargar Ejercicio Contable (Persistencia JSON)`**.
* Elige **`[1] Guardar ejercicio contable`** (por defecto guardará en `libro_diario.json`).
* El sistema creará automáticamente un respaldo previo (`libro_diario.json.bak`) antes de confirmar la escritura.

### Carga de un Ejercicio Existente
* En el submenú de persistencia, elige **`[2] Cargar ejercicio contable`**.
* Ingresa el nombre del archivo JSON. El sistema detectará automáticamente si es un archivo unificado moderno (v1.0/v1.1) o un libro diario legado, restaurando el inventario, partidas y nóminas de forma inmediata.

### Guardado al Salir
Si presionas `[0] Salir` en el menú principal y existen movimientos sin guardar, el orquestador te ofrecerá una confirmación preventiva para evitar pérdida de datos:
`¿Deseas guardar los cambios en 'libro_diario.json' antes de salir? (S/n):`
