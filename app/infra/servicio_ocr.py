import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import io
import os

class ServicioOCR:
    """
    Servicio de infraestructura encargado de la interacción con Tesseract OCR.
    """

    def extraer_texto_imagen(self, ruta_archivo: str) -> str:
        """
        Abre una imagen o PDF y extrae todo el texto legible.
        """
        if not os.path.exists(ruta_archivo):
            return ""

        try:
            texto_completo = ""
            ext = os.path.splitext(ruta_archivo)[1].lower()

            if ext == '.pdf':
                texto_completo = self._procesar_pdf(ruta_archivo)
            else:
                # Flujo normal para imágenes (JPG, PNG, etc.)
                imagen = Image.open(ruta_archivo)
                texto_completo = pytesseract.image_to_string(imagen, lang='spa')
            
            return texto_completo

        except Exception as e:
            print(f"🔥 [Error OCR] Falló al leer {ruta_archivo}: {e}")
            return ""

    def _es_texto_valido(self, texto: str) -> bool:
        """
        Verifica si el texto extraído parece válido (no es basura/mojibake).
        Heurística: Al menos el 50% de los caracteres deben ser alfanuméricos o espacios.
        """
        if not texto:
            return False
            
        caracteres_validos = 0
        total = len(texto)
        
        for char in texto:
            if char.isalnum() or char.isspace() or char in ".:,-/$%()":
                caracteres_validos += 1
                
        ratio = caracteres_validos / total
        return ratio > 0.5

    def _procesar_pdf(self, ruta_pdf: str) -> str:
        """
        Intenta extraer texto nativo del PDF. Si no hay suficiente texto
        o el texto parece corrupto, renderiza como imagen y ejecuta OCR.
        """
        texto_acumulado = []
        try:
            doc = fitz.open(ruta_pdf)
            for pagina in doc:
                # 1. Intentar extracción directa
                texto_pagina = pagina.get_text("text", sort=True)
                
                # 2. Verificar calidad del texto
                usar_ocr = False
                if len(texto_pagina.strip()) < 10:
                    usar_ocr = True
                elif not self._es_texto_valido(texto_pagina):
                    print(f"⚠️ Texto corrupto detectado en {os.path.basename(ruta_pdf)}, página {pagina.number + 1}. Forzando OCR.")
                    usar_ocr = True
                
                if usar_ocr:
                    # Renderizar página a imagen (pixmap) con ALTA resolución
                    pix = pagina.get_pixmap(matrix=fitz.Matrix(3, 3))
                    
                    # Convertir pixmap a bytes y luego a imagen PIL
                    img_data = pix.tobytes("png")
                    imagen = Image.open(io.BytesIO(img_data))
                    
                    # --- PREPROCESAMIENTO DE IMAGEN ---
                    imagen = imagen.convert('L') 
                    
                    # OCR de la página
                    custom_config = r'--oem 3 --psm 3' 
                    texto_pagina = pytesseract.image_to_string(imagen, lang='spa', config=custom_config)
                
                texto_acumulado.append(texto_pagina)
                
            doc.close()
            return "\n".join(texto_acumulado)
            
        except Exception as e:
            print(f"Error procesando PDF interno: {e}")
            return ""