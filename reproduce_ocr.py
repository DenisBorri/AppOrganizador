import os
import sys
from app.infra.servicio_ocr import ServicioOCR

def main():
    print("--- INICIANDO PRUEBA DE OCR ---")
    
    # 1. Configurar servicio
    servicio = ServicioOCR()
    
    # 2. Buscar archivos PDF en el directorio actual y subdirectorios directos
    directorio_actual = os.getcwd()
    directorios_a_buscar = [directorio_actual, os.path.join(directorio_actual, "facturas prueba")]
    
    archivos = []
    for d in directorios_a_buscar:
        if os.path.exists(d):
            pdfs = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith('.pdf')]
            archivos.extend(pdfs)
    
    if not archivos:
        print("❌ No se encontraron archivos PDF en el directorio actual para probar.")
        return

    print(f"📂 Se encontraron {len(archivos)} archivos PDF.")

    # 3. Procesar cada archivo y guardar resultado
    with open("ocr_debug_output.txt", "w", encoding="utf-8") as f_out:
        for archivo in archivos:
            print(f"🔄 Procesando: {archivo}...")
            ruta_completa = os.path.join(directorio_actual, archivo)
            
            texto = servicio.extraer_texto_imagen(ruta_completa)
            
            print(f"✅ Procesado. Longitud del texto: {len(texto)} caracteres.")
            
            f_out.write(f"--- INICIO REPORTE: {archivo} ---\n")
            f_out.write(texto)
            f_out.write(f"\n--- FIN REPORTE: {archivo} ---\n\n")

    print("\n📝 Prueba finalizada. Revisa el archivo 'ocr_debug_output.txt' para ver los resultados.")

if __name__ == "__main__":
    main()
