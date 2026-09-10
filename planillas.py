"""Punto de entrada principal para el cálculo de nómina y partidas contables."""
from typing import List

from planilla import (
    BONIFICACION_LEY,
    DEDUCCION_ISR_PERSONAL,
    IGSS_LABORAL,
    IGSS_PATRONAL,
    DatosEmpleado,
    PartidaContable,
    ResultadoPlanilla,
    calcular_boleta,
    calcular_isr_mensual,
    cargar_empleados_csv,
    crear_plantilla_csv_ejemplo,
    exportar_planilla_csv,
    generar_partida_contable,
    imprimir_boleta,
    imprimir_partida,
    money,
    solicitar_datos_interactivo,
)

# Alias para compatibilidad con scripts existentes
calcular_planilla = calcular_boleta
solicitar_datos_empleado = solicitar_datos_interactivo


def flujo_interactivo() -> List[ResultadoPlanilla]:
    """Captura secuencial de empleados desde la consola."""
    planillas: List[ResultadoPlanilla] = []
    while True:
        datos = solicitar_datos_interactivo()
        resultado = calcular_boleta(datos)
        planillas.append(resultado)
        imprimir_boleta(resultado)

        continuar = input("\n¿Deseas ingresar otro empleado? (s/n): ").strip().lower()
        if continuar not in ("s", "si", "y", "yes"):
            break
    return planillas


def menu_herramientas_csv(planillas_actuales: List[ResultadoPlanilla]) -> List[ResultadoPlanilla]:
    """Menú secundario para carga o exportación de archivos CSV (opción a futuro)."""
    print("\n" + "-" * 50)
    print("        HERRAMIENTAS CSV (OPCIONALES)")
    print("-" * 50)
    print("  [1] Generar archivo 'plantilla_empleados.csv' de ejemplo")
    print("  [2] Cargar y procesar empleados desde un archivo CSV")
    if planillas_actuales:
        print("  [3] Exportar planillas actuales a 'reporte_planilla.csv'")
    print("  [4] Volver al menú principal")

    opcion = input("\nSeleccione una opción: ").strip()

    if opcion == "1":
        ruta = input("Nombre o ruta del archivo [plantilla_empleados.csv]: ").strip() or "plantilla_empleados.csv"
        crear_plantilla_csv_ejemplo(ruta)
        print(f"  [OK] Plantilla generada exitosamente en: {ruta}")
    elif opcion == "2":
        ruta = input("Ruta del archivo CSV a cargar: ").strip()
        try:
            empleados = cargar_empleados_csv(ruta)
            if not empleados:
                print("  (!) No se encontraron empleados en el archivo.")
                return planillas_actuales
            nuevos_resultados = []
            for emp in empleados:
                res = calcular_boleta(emp)
                nuevos_resultados.append(res)
                imprimir_boleta(res)
            print(f"\n  [OK] Se procesaron {len(nuevos_resultados)} empleado(s) desde el archivo.")
            return planillas_actuales + nuevos_resultados
        except FileNotFoundError:
            print(f"  (!) El archivo '{ruta}' no fue encontrado.")
        except Exception as e:
            print(f"  (!) Error al procesar el archivo CSV: {e}")
    elif opcion == "3" and planillas_actuales:
        ruta = input("Nombre de archivo de destino [reporte_planilla.csv]: ").strip() or "reporte_planilla.csv"
        exportar_planilla_csv(planillas_actuales, ruta)
        print(f"  [OK] Planilla exportada exitosamente en: {ruta}")

    return planillas_actuales


def main():
    planillas_almacenadas: List[ResultadoPlanilla] = []

    print("=" * 65)
    print("        SISTEMA DE PLANILLAS Y PARTIDAS CONTABLES (GUATEMALA)")
    print("=" * 65)

    while True:
        print("\nOpciones principales:")
        print("  [1] Ingresar empleados interactivamente (Predeterminado)")
        print("  [2] Herramientas CSV (Carga / Plantilla / Exportación)")
        if planillas_almacenadas:
            print("  [3] Ver partida contable consolidada")
        print("  [0] Salir")

        eleccion = input("\nSeleccione opción [1]: ").strip()

        if eleccion in ("1", ""):
            nuevas = flujo_interactivo()
            planillas_almacenadas.extend(nuevas)
            if planillas_almacenadas:
                print(f"\nSe han acumulado {len(planillas_almacenadas)} planilla(s) en total.")
                partida = generar_partida_contable(planillas_almacenadas)
                imprimir_partida(partida)
        elif eleccion == "2":
            planillas_almacenadas = menu_herramientas_csv(planillas_almacenadas)
            if planillas_almacenadas:
                partida = generar_partida_contable(planillas_almacenadas)
                imprimir_partida(partida)
        elif eleccion == "3" and planillas_almacenadas:
            partida = generar_partida_contable(planillas_almacenadas)
            imprimir_partida(partida)
        elif eleccion == "0":
            print("\n¡Hasta pronto!")
            break
        else:
            print("Opción no válida. Intente nuevamente.")


if __name__ == "__main__":
    main()