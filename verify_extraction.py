import os
import sys
from app.core.procesador_facturas import ProcesadorFacturas
from app.core.entidades import Factura

def main():
    print("--- INICIANDO PRUEBA DE EXTRACCIÓN DE DATOS ---")
    procesador = ProcesadorFacturas()
    
    # Ajusta esta ruta si tus facturas están en otro lado
    directorio_prueba = os.path.join(os.getcwd(), "facturas prueba")
    
    if not os.path.exists(directorio_prueba):
        print(f"❌ No se encontró la carpeta: {directorio_prueba}")
        return

    # 1. Buscar archivos
    facturas = procesador.buscar_facturas_en_carpeta(directorio_prueba)
    print(f"📂 Se encontraron {len(facturas)} archivos para procesar.")
    
    for factura in facturas:
        print(f"\n🔄 Procesando: {factura.nombre_archivo}...")
        
        # Ejecutar procesamiento (OCR + Parsing)
        procesador.procesar_factura(factura)
        
        # Mostrar Resultados
        print(f"   📅 Fecha: {factura.fecha_emision}")
        print(f"   💰 Total: {factura.importe_total}")
        if factura.subtotal:
            print(f"      - Subtotal: {factura.subtotal}")
        if factura.importe_neto_gravado:
            print(f"      - Neto Gravado: {factura.importe_neto_gravado}")
        if factura.importe_iva:
            print(f"      - IVA: {factura.importe_iva}")
        if factura.importe_impuestos:
            print(f"      - Otros Impuestos: {factura.importe_impuestos}")
            
        print(f"   🏢 Emisor: {factura.cuit_emisor} (CUIT)")
        if factura.emisor:
             print(f"      - Razón Social: {factura.emisor}")
        print(f"   👤 Cliente: {factura.cuit_receptor} (CUIT)")
        print(f"   🧾 Tipo: {factura.tipo_factura}")

    print("\n--- FIN DE PRUEBA ---")

if __name__ == "__main__":
    main()
