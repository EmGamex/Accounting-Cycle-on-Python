"""Asistente para captura de partidas libres línea por línea con validación en vivo."""
from typing import Optional

from diario.engine import GestorLibroDiario
from diario.models import PartidaDiario
from diario.prompts import buscar_o_seleccionar_cuenta, pedir_fecha, pedir_monto

from ui import console, imprimir_alerta, imprimir_banner
from .comun import guardar_y_mostrar_partida


def registrar_partida_libre_asistida(gestor: GestorLibroDiario) -> Optional[PartidaDiario]:
    """Permite armar un asiento contable línea por línea con validación estricta de cuadre."""
    imprimir_banner("REGISTRO DE PARTIDA LIBRE (LÍNEA POR LÍNEA)", border_style="cyan")
    glosa = input("Glosa o explicación de la partida: ").strip() or "Asiento de diario personalizado"
    doc = input("Documento de soporte (opcional): ").strip() or None
    fecha = pedir_fecha()

    partida = PartidaDiario(
        numero=gestor.siguiente_numero,
        fecha=fecha,
        glosa=glosa,
        documento_soporte=doc,
    )

    console.print("\n[bold]INGRESO DE LÍNEAS (Escriba 'fin' en el código para terminar)[/bold]")
    while True:
        console.print(
            f"  Estado actual -> Debe: [green]Q {partida.total_debe:,.2f}[/green] | "
            f"Haber: [green]Q {partida.total_haber:,.2f}[/green] | Diferencia: [yellow]Q {partida.diferencia:,.2f}[/yellow]"
        )
        col = input("  ¿Imputar al Debe [D] o al Haber [H]? (o 'fin' para concluir): ").strip().upper()
        if col == "FIN":
            break
        if col not in ("D", "H"):
            imprimir_alerta("Opción no válida. Ingrese D para Debe o H para Haber.")
            continue

        cod, nom = buscar_o_seleccionar_cuenta("  Código o nombre de cuenta", gestor=gestor)
        monto = pedir_monto(f"  Monto a registrar en el {'DEBE' if col == 'D' else 'HABER'}: Q ")

        if col == "D":
            partida.agregar_cargo(cod, nom, monto)
        else:
            partida.agregar_abono(cod, nom, monto)

    return guardar_y_mostrar_partida(gestor, partida, "Partida libre registrada exitosamente")
