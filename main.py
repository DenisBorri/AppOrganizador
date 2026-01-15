import customtkinter as ctk
from app.ui.ventana_principal import VentanaPrincipal

# Configuración Global de Estilo
ctk.set_appearance_mode("Dark")  # Modos: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Temas: "blue" (standard), "green", "dark-blue"

def iniciar_app():
    """
    Función de arranque. 
    Aquí inyectaremos las dependencias en el futuro.
    """
    print(">> Iniciando Sistema RPA de Facturas...")
    
    # Instanciamos la ventana principal
    app = VentanaPrincipal()
    
    # Iniciamos el bucle principal de eventos
    app.mainloop()

if __name__ == "__main__":
    iniciar_app()