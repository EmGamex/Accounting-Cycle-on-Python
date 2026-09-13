"""Excepciones de dominio para el subsistema de persistencia contable."""


class PersistenciaError(Exception):
    """Excepción base para todos los errores del subsistema de persistencia."""
    pass


class FormatoArchivoInvalidoError(PersistenciaError):
    """Se lanza cuando la estructura del archivo o JSON no coincide con el formato esperado."""
    pass


class VersionEsquemaIncompatibleError(PersistenciaError):
    """Se lanza cuando la versión del esquema del archivo no es compatible."""
    pass


class IntegridadDatosError(PersistenciaError):
    """Se lanza cuando los datos cargados violan reglas de integridad o consistencia contable."""
    pass


class EscrituraArchivoError(PersistenciaError):
    """Se lanza cuando ocurre un fallo al escribir o sincronizar el archivo en disco."""
    pass
