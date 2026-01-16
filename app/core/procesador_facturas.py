from typing import List
import re
from app.core.entidades import Factura
from app.infra.repositorio_archivos import RepositorioArchivos
from app.infra.servicio_ocr import ServicioOCR

class ProcesadorFacturas:
    """
    Caso de Uso: Coordinar la búsqueda y el procesamiento de facturas.
    """

    def __init__(self):
        # Inyección de dependencias
        self.repositorio = RepositorioArchivos()
        self.ocr = ServicioOCR()

    def buscar_facturas_en_carpeta(self, ruta_carpeta: str) -> List[Factura]:
        """
        1. Pide al repositorio las rutas de archivos.
        2. Convierte esas rutas en objetos 'Factura' vacíos.
        """
        rutas_archivos = self.repositorio.obtener_rutas_facturas(ruta_carpeta)
        
        lista_facturas = []
        if rutas_archivos:
            for ruta in rutas_archivos:
                nombre_archivo = ruta.split("\\")[-1] 
                
                nueva_factura = Factura(
                    ruta_archivo=ruta,
                    nombre_archivo=nombre_archivo
                )
                lista_facturas.append(nueva_factura)
            
        return lista_facturas

    def procesar_factura(self, factura: Factura) -> Factura:
        """
        Toma una factura, extrae su texto y parsea los datos clave.
        """
        # 1. Extraer texto crudo (ahora intentará texto nativo con orden visual)
        texto_extraido = self.ocr.extraer_texto_imagen(factura.ruta_archivo)
        factura.texto_crudo = texto_extraido
        
        # 2. Parsear datos del texto
        if texto_extraido and len(texto_extraido) > 10:
            factura.es_valida = True
            datos = self._parsear_datos(texto_extraido)
            
            # Asignar datos parseados a la entidad
            factura.importe_total = datos.get("importe_total")
            factura.importe_iva = datos.get("importe_iva")
            factura.subtotal = datos.get("subtotal")
            factura.importe_neto_gravado = datos.get("importe_neto_gravado")
            factura.importe_impuestos = datos.get("importe_impuestos")
            
            factura.fecha_emision = datos.get("fecha_emision")
            factura.tipo_factura = datos.get("tipo_factura")
            factura.emisor = datos.get("emisor")
            factura.receptor = datos.get("receptor")
            factura.cuit_emisor = datos.get("cuit_emisor")
            factura.cuit_receptor = datos.get("cuit_receptor")

        return factura

    def _parsear_datos(self, texto: str) -> dict:
        """
        Aplica Expresiones Regulares para extraer información estructurada con lógica mejorada.
        """
        datos = {}
        
        # Helper para limpiar y convertir monto
        def limpiar_monto(matches):
            return self._extraer_monto(matches)

        # Helper para búsqueda "laxa": Label ... (texto) ... Numero
        # Usamos re.DOTALL para que . coincida con \n
        def buscar_primer_numero(label_pattern, texto_fuente):
            # Busca el label, seguido de cualquier cosa (no codiciosa), seguido de un numero formateado
            # Exigimos que el numero tenga al menos un punto o coma para evitar "123" basura
            # O que tenga al menos 4 digitos
            regex = label_pattern + r".*?([\d\.,]+)"
            match = re.search(regex, texto_fuente, re.IGNORECASE | re.DOTALL)
            if match:
                return limpiar_monto([match.group(1)])
            return None

        # --- 1. Importe Total ---
        # Prioridad: Buscar monto con símbolo $ explícito (ej. $ 6.657.200,00)
        # Regex busca "Total" ... texto ... "$" ... Numero
        patron_total_con_simbolo = r"(?:Total|Totales)(?:es)?.*?\$ ?([\d\.,]+)"
        match_total_simbolo = re.search(patron_total_con_simbolo, texto, re.IGNORECASE | re.DOTALL)
        
        candidatos_total = []
        if match_total_simbolo:
            candidatos_total.append(match_total_simbolo.group(1))
        
        # Si no encontramos con $, buscamos Total general
        if not candidatos_total:
             patron_total_simple = r"(?:Importe\s+Total|Total|Totales)(?:es)?.*?(?<![\d])([\d\.,]{4,})"
             matches_simple = re.findall(patron_total_simple, texto, re.IGNORECASE | re.DOTALL)
             if matches_simple:
                 for m in matches_simple:
                     val = m.strip()
                     # Filtrar IDs largos (barcodes)
                     if len(val.replace('.','').replace(',','')) > 9 and ('.' not in val and ',' not in val):
                         continue
                     candidatos_total.append(val)
        
        datos["importe_total"] = limpiar_monto(candidatos_total)

        # --- 1.1 Sub-Total ---
        if not datos.get("subtotal"):
             datos["subtotal"] = buscar_primer_numero(r"(?:Sub[- ]?Total|Subtotal)", texto)

        # --- 1.2 Neto Gravado ---
        if not datos.get("importe_neto_gravado"):
            # Ojo: a veces coincide con el mismo texto.
            datos["importe_neto_gravado"] = buscar_primer_numero(r"(?:Neto\s+Gravado|Neto)", texto)

        # --- 1.3 Impuestos ---
        if not datos.get("importe_impuestos"):
            datos["importe_impuestos"] = buscar_primer_numero(r"(?:Ingresos\s+Brutos|Impuestos|Percepciones)", texto)
        
        # --- 1.4 IVA ---
        if not datos.get("importe_iva"):
            # Prioridad: IVA Insc.
            iva = buscar_primer_numero(r"(?:I\.?V\.?A\.?)\s*(?:Insc\.?|Responsable Inscripto|21%)", texto)
            datos["importe_iva"] = iva

        # --- 2. Fecha de Emisión ---
        # Permitir salto de linea: "Fecha \n 12/12/2023"
        match_fecha = re.search(r"(?:Fecha\s+de\s+Emisi[óo]n|Fecha)\s*[:]?\s*\n?\s*(\d{2}[/-]\d{2}[/-]\d{4})", texto, re.IGNORECASE)
        if match_fecha:
            datos["fecha_emision"] = match_fecha.group(1).replace('-', '/')

        # --- 3. Receptor (Cliente) ---
        # Prioridad: "Señor (es):", "Apellido y Nombre:", "Razon Social:"
        # Permitimos saltos de línea y texto intermedio corto
        patron_cliente = r"(?:Señor\s*\(es\)|Apellido y Nombre|Razón Social|Cliente|Sr\.)[\s\.:]*\n?\s*(?P<nombre>.+)"
        match_cliente = re.search(patron_cliente, texto, re.IGNORECASE)
        if match_cliente:
            raw_receptor = match_cliente.group("nombre").strip()
            # Limpieza: si el nombre es muy largo o contiene keywords de otra cosa, cortar
            # Cortar en "Fecha", "Domicilio", "Condición"
            cortes = ["Fecha", "Domicilio", "Condici", "C.U.I.T"]
            for c in cortes:
                if c.lower() in raw_receptor.lower():
                    raw_receptor = re.split(c, raw_receptor, flags=re.IGNORECASE)[0]
            
            datos["receptor"] = re.sub(r"^\(\d+\)\s*", "", raw_receptor).strip()

        # --- 4. CUITs ---
        # Regex tolerante a ruido OCR: "C.U.I.T. N*", "CUIT:", "30-..." directo si está etiquetado
        # Buscamos patrones numéricos de CUIT (XX-XXXXXXXX-X)
        matches_cuit_raw = re.findall(r"\b(\d{2}[- ]?\d{8}[- ]?\d)\b", texto)
        
        # Filtramos para tener formato estandar XX-XXXXXXXX-X
        cuits_validos = []
        for c in matches_cuit_raw:
             # Normalizamos a guiones
             clean = c.replace(' ', '')
             if len(clean) == 11 and '-' not in clean:
                 # Añadir guiones hipotéticos 20123456789 -> 20-12345678-9
                 clean = f"{clean[:2]}-{clean[2:10]}-{clean[10]}"
             
             if len(clean) == 13 and clean[2] == '-' and clean[11] == '-':
                 if clean not in cuits_validos:
                     cuits_validos.append(clean)
        
        datos["todos_cuits"] = cuits_validos # Debug interpreno

        # Asignación Inteligente de CUITs
        # 1. Buscar CUIT explícito de Receptor cerca de "Cliente"
        # 2. Asumir CUIT Emisor es el primero que aparece en la cabecera
        
        if cuits_validos:
            # Estrategia simple mejorada:
            # El CUIT del emisor suele estar arriba (primeros 50% caracteres o primera coincidencia)
            # El CUIT del receptor suele estar cerca de los datos del cliente
            
            datos["cuit_emisor"] = cuits_validos[0]
            
            if len(cuits_validos) > 1:
                # Si hay más de uno, validamos
                # Si el "Cliente" fue detectado, buscamos un CUIT cercano a ese match?
                # Por simplicidad: Segundo CUIT distinto es Receptor
                if cuits_validos[1] != cuits_validos[0]:
                    datos["cuit_receptor"] = cuits_validos[1]

        # --- 5. Emisor (Fallback mejorado) ---
        # --- 5. Emisor (Fallback mejorado) ---
        if "emisor" not in datos:
            # Buscamos en las primeras líneas algo que parezca una empresa
            # Ignoramos líneas de una sola palabra "A", "ORIGINAL", fechas
            lineas = [l.strip() for l in texto.split('\n') if l.strip()]
            for l in lineas[:25]: # Ampliado a 25 lineas (Desab aparecia en la 16)
                l_upper = l.upper()
                keywords_ignoradas = [
                    "ORIGINAL", "DUPLICADO", "FACTURA", "FECHA", "CUIT", "IIBB", 
                    "PAGINA", "HOJA", "DOCUMENTO", "N°", "NRO", "NUMERO", "COD", "LUGAR", "SUCURSAL"
                ]
                
                # Reglas de descarte:
                if len(l) < 3: continue
                if any(k in l_upper for k in keywords_ignoradas): continue
                if re.match(r"^\d", l): continue # Empieza con numero
                
                # Si llegamos aquí, es candidato fuerte
                datos["emisor"] = l
                break

        # --- 6. Tipo de Factura ---
        # Buscamos la letra sola en un recuadro o "COD. 0XX"
        if "tipo_factura" not in datos:
            if re.search(r"COD\.\s*011", texto) or re.search(r"\bFACTURA\s+C\b", texto, re.IGNORECASE):
                datos["tipo_factura"] = "C"
            elif re.search(r"COD\.\s*001", texto) or re.search(r"\bFACTURA\s+A\b", texto, re.IGNORECASE):
                datos["tipo_factura"] = "A"
            elif re.search(r"COD\.\s*006", texto) or re.search(r"\bFACTURA\s+B\b", texto, re.IGNORECASE):
                datos["tipo_factura"] = "B"
            else:
                 # Busqueda de letra solitaria arriba
                 match_letra = re.search(r"^\s*([ABC])\s*$", texto, re.MULTILINE)
                 if match_letra:
                      datos["tipo_factura"] = match_letra.group(1)

        return datos

    def _extraer_monto(self, matches: List[str]) -> float:
        """
        Helper para limpiar y convertir string a float desde una lista de candidatos.
        Prioriza el último candidato si hay varios.
        """
        if not matches:
            return None
            
        for candidato in reversed(matches):
            raw_val = candidato.strip().replace(' ', '')
            if not any(char.isdigit() for char in raw_val):
                continue
                
            try:
                val_float = 0.0
                if ',' in raw_val and '.' in raw_val:
                    if raw_val.rfind(',') > raw_val.rfind('.'):
                        val_float = float(raw_val.replace('.', '').replace(',', '.'))
                    else:
                        val_float = float(raw_val.replace(',', ''))
                elif ',' in raw_val:
                     if raw_val.count(',') > 1:
                         val_float = float(raw_val.replace(',', ''))
                     elif len(raw_val) - raw_val.rfind(',') == 3:
                         val_float = float(raw_val.replace(',', '.'))
                     else:
                         val_float = float(raw_val.replace(',', ''))
                else:
                    if raw_val.count('.') > 1:
                        val_float = float(raw_val.replace('.', ''))
                    else:
                         val_float = float(raw_val)
                return val_float
            except:
                continue
        return None