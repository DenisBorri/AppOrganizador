from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Factura:
    """
    Entidad que representa una factura en el sistema.
    No contiene lógica de base de datos ni de interfaz, solo datos puros.
    """
    ruta_archivo: str
    nombre_archivo: str
    fecha_procesamiento: datetime = field(default_factory=datetime.now)
    
    # Estos campos se llenarán después del OCR
    texto_crudo: Optional[str] = None
    
    # Datos extraídos
    tipo_factura: Optional[str] = None
    fecha_emision: Optional[str] = None
    importe_total: Optional[float] = None
    importe_iva: Optional[float] = None
    subtotal: Optional[float] = None
    importe_neto_gravado: Optional[float] = None
    importe_impuestos: Optional[float] = None
    
    # Entidades
    emisor: Optional[str] = None
    receptor: Optional[str] = None
    cuit_emisor: Optional[str] = None
    cuit_receptor: Optional[str] = None
    
    # Deprecated / Legacy (mantener por compatibilidad si es necesario)
    total_encontrado: Optional[float] = None
    proveedor: Optional[str] = None
    es_valida: bool = False

    def __post_init__(self):
        """Validaciones básicas al crear la entidad."""
        if not self.ruta_archivo:
            raise ValueError("La factura debe tener una ruta de archivo válida.")