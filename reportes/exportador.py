"""Utilidades de exportación y guardado físico de reportes contables a disco."""
import os


def exportar_archivo_texto(contenido: str, ruta_archivo: str) -> str:
    """Guarda contenido de texto en el archivo especificado usando UTF-8.

    Args:
        contenido: Cadena de texto a escribir.
        ruta_archivo: Ruta relativa o absoluta del archivo de destino.

    Returns:
        Ruta absoluta del archivo guardado.
    """
    directorio = os.path.dirname(os.path.abspath(ruta_archivo))
    if directorio and not os.path.exists(directorio):
        os.makedirs(directorio, exist_ok=True)

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(contenido)

    return os.path.abspath(ruta_archivo)
