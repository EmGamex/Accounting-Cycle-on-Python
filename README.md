# Sistema Integral de Contabilidad Automatizada (Guatemala)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](tests/)
[![Marco Normativo](https://img.shields.io/badge/normativa-Guatemala%20(SAT%20%7C%20IGSS)-orange.svg)](docs/reference/legislacion_y_tasas_guatemala.md)
[![Docs](https://img.shields.io/badge/docs-Di%C3%A1taxis-purple.svg)](docs/README.md)

Suite modular en Python que automatiza el **Ciclo Contable Clásico** (Apertura → Diario → Mayor → Balances) bajo la legislación mercantil y tributaria de **Guatemala** (Código de Comercio, SAT, IGSS y NIIF para PYMES). Garantiza precisión monetaria estricta con `decimal.Decimal` y exportación profesional a Microsoft Excel (`.xlsx`).

---

## Características Principales

- **Precisión financiera absoluta**: Aritmética con `Decimal` (cero errores de punto flotante) y validación inviolable de partida doble ($\sum \text{Debe} = \sum \text{Haber}$).
- **Generación en cascada**: El Libro Diario alimenta de forma desatendida el Mayor (T-Gráficas y 3 columnas), el Balance de 4 Columnas y el Balance General.
- **Nóminas y retenciones de ley**: Cálculo automático de IGSS (Laboral 4.83% / Patronal 12.67%), Bonificación Incentivo Q250, horas extras y retenciones ISR.
- **Exportación contable a Excel**: Generación de reportes `.xlsx` auditables con formatos y fórmulas automáticas.
- **Interfaz enriquecida y persistencia**: Consola interactiva con `rich` y guardado/recuperación en JSON para reanudar ejercicios.

---

## Inicio Rápido

```bash
# 1. Clonar el repositorio
git clone https://github.com/EmGamex/Accounting-Cycle-on-Python.git
cd Accounting-Cycle-on-Python

# 2. Crear y activar entorno virtual
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1 | Linux/macOS: source .venv/bin/activate

# 3. Instalar dependencias y ejecutar
pip install -r requirements.txt
python main.py
```

> [!TIP]
> Puedes importar colaboradores masivamente usando el archivo de ejemplo [`plantilla_empleados.csv`](plantilla_empleados.csv).

---

## Documentación

La documentación completa del proyecto está organizada bajo el marco **Diátaxis** en [`docs/`](docs/README.md):

- **[Tutoriales](docs/tutorials/)**: [Tu Primer Ciclo Contable en 15 Minutos](docs/tutorials/01_primer_ciclo_contable.md) (guía paso a paso desde apertura hasta nómina).
- **[Guías Prácticas](docs/how-to/)**: [Apertura de Empresa](docs/how-to/registrar_apertura_empresa.md) | [Procesamiento de Planillas](docs/how-to/procesar_nomina_y_planillas.md) | [Partidas de Diario](docs/how-to/estructurar_partidas_diario.md) | [Extender Catálogo](docs/how-to/extender_catalogo_cuentas.md).
- **[Referencia Técnica](docs/reference/)**: [Catálogo NIIF/SAT](docs/reference/catalogo_cuentas.md) | [Modelos de Datos](docs/reference/modelos_y_dataclasses.md) | [Tasas y Leyes de Guatemala](docs/reference/legislacion_y_tasas_guatemala.md).
- **[Explicación y Arquitectura](docs/explanation/)**: [Ciclo Contable y Partida Doble](docs/explanation/ciclo_contable_y_partida_doble.md) | [Precisión Decimal](docs/explanation/precision_decimal_financiera.md) | [Diseño Modular del Sistema](docs/explanation/arquitectura_del_sistema.md).

---

## Pruebas

```bash
pytest
```
