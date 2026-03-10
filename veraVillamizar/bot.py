import customtkinter as ctk
import google.generativeai as genai
import threading
from datetime import datetime

# --- CONFIGURACIÓN VISUAL (ESTILO WHATSAPP) ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green") # Tema verde nativo

# Colores WhatsApp Dark Mode
C_BG_MAIN = "#111b21"      # Fondo general
C_BG_CHAT = "#0b141a"      # Fondo del chat (donde van los mensajes)
C_BG_INPUT = "#202c33"     # Barra de escritura
C_BUBBLE_USER = "#005c4b"  # Burbuja verde (Usuario)
C_BUBBLE_BOT = "#202c33"   # Burbuja gris (IA)
C_TEXT_MAIN = "#e9edef"
C_ACCENT = "#00a884"       # Verde WhatsApp brillante

# --- 🔐 CONFIGURACIÓN GEMINI ---
GEMINI_API_KEY = "" # <--- ¡TU CLAVE VA AQUÍ!

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = None

# --- 🧠 CEREBRO LEGAL (PROMPT DEL SISTEMA) ---
INSTRUCCIONES_SISTEMA = """
Actúa como el asistente virtual oficial de la firma de abogados "Vera Villamizar Abogados".
TU PERFIL:
- Ubicación: Floridablanca y Bucaramanga, Santander, Colombia.
- Tono: Profesional, empático, seguro, pero cercano (estilo WhatsApp).
- Objetivo: Filtrar clientes, responder dudas básicas y agendar citas.

REGLAS DE ORO:
1. NO des consejos legales vinculantes (ej: "Ganarás el caso"). Di "Según nuestra experiencia..." o "Es vital revisar el expediente".
2. Si el caso suena complejo (demandas, penal, familia conflictivo), sugiere agendar una consulta presencial en Floridablanca.
3. Tus horarios son Lunes a Viernes 8am - 6pm.
4. Sé conciso. Los mensajes de WhatsApp no deben ser párrafos eternos. Usa emojis moderados (⚖️, 📅, 🤝).

Si te saludan, preséntate brevemente como el asistente de Vera Villamizar.
"""

class WhatsAppSimulator(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vera Villamizar - Chat de Soporte (Simulación)")
        self.geometry("450x700")
        self.configure(fg_color=C_BG_MAIN)
        self.resizable(True, True)

        # Inicializar sesión de chat con memoria
        if model:
            self.chat_session = model.start_chat(history=[
                {"role": "user", "parts": [INSTRUCCIONES_SISTEMA]},
                {"role": "model", "parts": ["Entendido. Soy el asistente de Vera Villamizar Abogados. Estoy listo para atender consultas con profesionalismo y empatía."]}
            ])
        else:
            self.chat_session = None

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. ENCABEZADO (Perfil)
        self.header = ctk.CTkFrame(self, fg_color=C_BG_INPUT, height=60, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        
        # Foto de perfil simulada (Círculo) y Nombre
        ctk.CTkLabel(self.header, text="⚖️", font=("Arial", 30)).pack(side="left", padx=(15, 10), pady=10)
        
        info_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        info_frame.pack(side="left", pady=10)
        ctk.CTkLabel(info_frame, text="Vera Villamizar Abogados", font=("Helvetica", 16, "bold"), text_color=C_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(info_frame, text="En línea", font=("Helvetica", 12), text_color=C_ACCENT).pack(anchor="w")

        # 2. ÁREA DE CHAT (Scrollable)
        self.chat_area = ctk.CTkScrollableFrame(self, fg_color=C_BG_CHAT, corner_radius=0)
        self.chat_area.grid(row=1, column=0, sticky="nsew")

        # 3. ÁREA DE INPUT (Abajo)
        self.input_area = ctk.CTkFrame(self, fg_color=C_BG_INPUT, height=60, corner_radius=0)
        self.input_area.grid(row=2, column=0, sticky="ew")

        self.entry_msg = ctk.CTkEntry(
            self.input_area, 
            placeholder_text="Escribe un mensaje...",
            font=("Helvetica", 14),
            fg_color="#2a3942", border_width=0, text_color="white",
            height=40, corner_radius=20
        )
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.entry_msg.bind("<Return>", lambda e: self.send_message())

        self.btn_send = ctk.CTkButton(
            self.input_area, text="➤", width=40, height=40,
            fg_color=C_ACCENT, hover_color="#008f6f",
            corner_radius=20, font=("Arial", 18),
            command=self.send_message
        )
        self.btn_send.pack(side="right", padx=(0, 10), pady=10)

    def send_message(self):
        msg = self.entry_msg.get().strip()
        if not msg: return

        # 1. Mostrar mensaje del usuario (Derecha)
        self.add_bubble(msg, is_user=True)
        self.entry_msg.delete(0, "end")

        # 2. Llamar a la IA en hilo separado
        threading.Thread(target=self.get_ai_reply, args=(msg,), daemon=True).start()

    def get_ai_reply(self, user_msg):
        if not self.chat_session:
            self.after(0, lambda: self.add_bubble("Error: Sin API Key", is_user=False))
            return

        try:
            # Enviar mensaje a Gemini manteniendo historial
            response = self.chat_session.send_message(user_msg)
            reply = response.text
            
            # Actualizar UI
            self.after(0, lambda: self.add_bubble(reply, is_user=False))
        except Exception as e:
            self.after(0, lambda: self.add_bubble(f"Error de red: {e}", is_user=False))

    def add_bubble(self, text, is_user):
        # Crear un frame para la burbuja
        bubble_color = C_BUBBLE_USER if is_user else C_BUBBLE_BOT
        align = "e" if is_user else "w" # East (Der) o West (Izq)
        
        # Contenedor para alinear
        container = ctk.CTkFrame(self.chat_area, fg_color="transparent")
        container.pack(fill="x", pady=5, padx=10)

        # La burbuja en sí
        bubble = ctk.CTkLabel(
            container, 
            text=text, 
            fg_color=bubble_color,
            text_color=C_TEXT_MAIN,
            font=("Helvetica", 14),
            corner_radius=10,
            wraplength=300, # Ajuste de línea para textos largos
            justify="left"
        )
        
        # Empaquetado con padding interno simulado
        if is_user:
            bubble.pack(side="right", ipadx=10, ipady=5)
        else:
            bubble.pack(side="left", ipadx=10, ipady=5)
        
        # Auto-scroll al fondo
        self.chat_area._parent_canvas.yview_moveto(1.0)

if __name__ == "__main__":
    app = WhatsAppSimulator()
    app.mainloop()