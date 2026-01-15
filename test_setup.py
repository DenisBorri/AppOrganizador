import sys
import os
import pytesseract
from app.infra.repositorio_archivos import RepositorioArchivos

# --- CONFIGURACIÓN DE RUTA DE TESSERACT (Opcional si ya está en el PATH) ---
# Si el test falla, descomenta la siguiente línea y pon tu ruta real:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def probar_tesseract():
    print("--- 1. Probando Tesseract ---")
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract detectado correctamente. Versión: {version}")
        return True
    except pytesseract.TesseractNotFoundError:
        print("❌ ERROR CRÍTICO: Python no encuentra Tesseract.")
        print("   Solución: Asegúrate de haber agregado la ruta al PATH de Windows")
        print("   o configura 'tesseract_cmd' manualmente en el código.")
        return False
    except Exception as e:
        print(f"❌ Error desconocido con Tesseract: {e}")
        return False

def probar_lectura_archivos():
    print("\n--- 2. Probando Lectura de Archivos ---")
    # Usaremos la carpeta actual para probar
    repo = RepositorioArchivos()
    carpeta_actual = os.getcwd()
    print(f"Escaneando carpeta actual: {carpeta_actual}")
    
    archivos = repo.obtener_rutas_facturas(carpeta_actual)
    
    if archivos is not None:
        print(f"✅ Sistema de archivos funcionando. Archivos detectados: {len(archivos)}")
    else:
        print("❌ El repositorio devolvió None.")

if __name__ == "__main__":
    print("🤖 INICIANDO DIAGNÓSTICO DEL SISTEMA...\n")
    exito_ocr = probar_tesseract()
    probar_lectura_archivos()
    
    if exito_ocr:
        print("\n✨ TODO LISTO. Puedes continuar con el desarrollo.")
    else:
        print("\n⚠️ REVISA LA INSTALACIÓN DE TESSERACT ANTES DE SEGUIR.")