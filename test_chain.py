import sys
import os

# Add current dir to path just in case, though python does this by default for the script dir
sys.path.append(os.getcwd())

print(f"Python: {sys.executable}")
try:
    from app.infra.servicio_ocr import ServicioOCR
    print("Imported ServicioOCR successfully")
    s = ServicioOCR()
    print("Instance created")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"Other error: {e}")
