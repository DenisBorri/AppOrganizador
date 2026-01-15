import os
from pathlib import Path
from typing import List

class RepositorioArchivos:
    """
    Encargado de las operaciones de lectura/escritura en el sistema de archivos.
    Sigue el principio de Responsabilidad Única.
    """

    def __init__(self):
        # Extensiones permitidas para procesar
        self.extensiones_validas = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff'}

    def obtener_rutas_facturas(self, ruta_carpeta: str) -> List[str]:
        """
        Escanea una carpeta y devuelve una lista con las rutas completas
        de los archivos válidos (imágenes/PDF).
        """
        archivos_encontrados = []
        path_carpeta = Path(ruta_carpeta)

        if not path_carpeta.exists():
            print(f"❌ [Error Infra] La carpeta no existe: {ruta_carpeta}")
            return []

        try:
            # Iteramos sobre los archivos en el directorio
            for archivo in path_carpeta.iterdir():
                if archivo.is_file() and archivo.suffix.lower() in self.extensiones_validas:
                    archivos_encontrados.append(str(archivo.absolute()))
            
            print(f"✅ [Infra] Se encontraron {len(archivos_encontrados)} documentos en {ruta_carpeta}")
            return archivos_encontrados

        except PermissionError:
            print(f"⛔ [Error Infra] Permiso denegado para acceder a: {ruta_carpeta}")
            return []
        except Exception as e:
            print(f"🔥 [Error Infra] Error inesperado leyendo archivos: {e}")
            return []