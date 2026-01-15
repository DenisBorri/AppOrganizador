import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from typing import List
from app.core.procesador_facturas import ProcesadorFacturas
from app.core.entidades import Factura

class VentanaPrincipal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Gestor de Facturas - PythonProyects")
        self.geometry("1000x700")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.procesador = ProcesadorFacturas()
        self.facturas_en_memoria: List[Factura] = []
        
        # Diccionario para guardar referencias a los labels de estado de cada fila
        # Clave: índice de la lista, Valor: widget Label
        self.widgets_estado = {} 

        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        # --- Panel Lateral ---
        self.frame_lateral = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.frame_lateral.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.frame_lateral, text="RPA Facturas", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20)

        # --- Área Principal ---
        self.frame_principal = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_principal.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(self.frame_principal, text="Gestión de Documentos", font=ctk.CTkFont(size=24)).pack(pady=10, anchor="w")

        # Botonera
        self.frame_botones = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        self.frame_botones.pack(fill="x", pady=10)

        self.btn_seleccionar = ctk.CTkButton(self.frame_botones, text="📂 1. Seleccionar Carpeta", command=self.evento_seleccionar_carpeta)
        self.btn_seleccionar.pack(side="left", padx=(0, 10))

        self.btn_procesar = ctk.CTkButton(
            self.frame_botones, 
            text="⚙️ 2. Procesar (OCR)", 
            fg_color="green", 
            state="disabled", # Deshabilitado hasta que haya archivos
            command=self.evento_iniciar_procesamiento
        )
        self.btn_procesar.pack(side="left")

        # Lista Scrollable
        ctk.CTkLabel(self.frame_principal, text="Documentos Detectados:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 5), anchor="w")
        self.lista_scroll = ctk.CTkScrollableFrame(self.frame_principal, label_text="Estado del Proceso")
        self.lista_scroll.pack(fill="both", expand=True)

    def evento_seleccionar_carpeta(self) -> None:
        carpeta = filedialog.askdirectory()
        if not carpeta: return

        try:
            self.facturas_en_memoria = self.procesador.buscar_facturas_en_carpeta(carpeta)
            self._mostrar_lista_inicial()
            
            if self.facturas_en_memoria:
                self.btn_procesar.configure(state="normal") # Habilitamos el botón procesar
                messagebox.showinfo("Carga", f"Cargados {len(self.facturas_en_memoria)} archivos listos para procesar.")
            else:
                self.btn_procesar.configure(state="disabled")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _mostrar_lista_inicial(self) -> None:
        for w in self.lista_scroll.winfo_children(): w.destroy()
        self.widgets_estado = {} # Reiniciar mapeo

        for idx, factura in enumerate(self.facturas_en_memoria):
            fila = ctk.CTkFrame(self.lista_scroll)
            fila.pack(fill="x", pady=2, padx=5)
            
            ctk.CTkLabel(fila, text=factura.nombre_archivo, anchor="w").pack(side="left", padx=10)
            
            # Guardamos referencia a este label para cambiarlo luego
            lbl_estado = ctk.CTkLabel(fila, text="⏳ Pendiente", text_color="gray")
            lbl_estado.pack(side="right", padx=10)
            
            self.widgets_estado[idx] = lbl_estado

    def evento_iniciar_procesamiento(self) -> None:
        """Inicia el hilo de procesamiento para no congelar la UI."""
        self.btn_seleccionar.configure(state="disabled")
        self.btn_procesar.configure(state="disabled", text="Procesando...")
        
        # Lanzamos el hilo
        hilo = threading.Thread(target=self._logica_procesamiento_background)
        hilo.start()

    def _logica_procesamiento_background(self) -> None:
        """Esta función corre en paralelo (Segundo Hilo)."""
        errores = 0
        
        for idx, factura in enumerate(self.facturas_en_memoria):
            # Cambiar estado visual a "Analizando..."
            self.widgets_estado[idx].configure(text="🔍 Analizando...", text_color="orange")
            
            try:
                # Llamada pesada al CORE -> INFRA
                self.procesador.procesar_factura(factura)
                
                # Si volvió texto, éxito
                if factura.es_valida:
                    print(f"Texto detectado en {factura.nombre_archivo}:\n{factura.texto_crudo[:50]}...") # Log en consola
                    self.widgets_estado[idx].configure(text="✅ Leído", text_color="green")
                else:
                    self.widgets_estado[idx].configure(text="⚠️ Vacío", text_color="yellow")
            
            except Exception as e:
                errores += 1
                self.widgets_estado[idx].configure(text="❌ Error", text_color="red")
                print(f"Error procesando {factura.nombre_archivo}: {e}")

        # Restaurar botones (Usamos 'after' para volver al hilo principal de la UI de forma segura)
        self.after(0, lambda: self._finalizar_ui_post_proceso(errores))

    def _finalizar_ui_post_proceso(self, errores: int):
        self.btn_seleccionar.configure(state="normal")
        self.btn_procesar.configure(state="normal", text="⚙️ 2. Procesar (OCR)")
        
        if errores == 0:
            messagebox.showinfo("Finalizado", "Procesamiento completado exitosamente.")
        else:
            messagebox.showwarning("Finalizado", f"Proceso terminado con {errores} errores.")