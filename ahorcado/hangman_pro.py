import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import google.generativeai as genai
import threading
import json
import time
import unicodedata
import os # Necesario para gestión de archivos

# --- CONFIGURACIÓN DE COLORES Y ESTILO ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Paleta Cyberpunk / Neon
C_BG = "#050505"           
C_ACCENT_1 = "#00E5FF"     # Cyan Neon
C_ACCENT_2 = "#FF2E63"     # Rosa/Rojo Neon (Muerte)
C_ACCENT_3 = "#F9F871"     # Amarillo
C_TEXT = "#E0E0E0"
C_PANEL = "#121212"

# --- 🔐 CONFIGURACIÓN GEMINI ---
GEMINI_API_KEY = "AIzaSyBjZlDyniP4ZUr3NTBHF0Kpfv2y1g4sNrw" # <--- ¡PEGA TU API KEY AQUÍ!

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = None

# --- 💾 GESTOR DE HISTORIAL (PERSISTENCIA) ---
HISTORY_FILE = "hangman_history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_word_to_history(theme, word):
    history = load_history()
    theme_key = theme.lower().strip()
    
    if theme_key not in history:
        history[theme_key] = []
    
    if word not in history[theme_key]:
        history[theme_key].append(word)
        
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

# --- 🧠 LÓGICA DEL JUEGO (MODELO) ---
class GameModel:
    def __init__(self):
        self.target_word = ""
        self.display_word = [] 
        self.lives = 6 # AHORA SON 6 VIDAS
        self.guessed_letters = set()
        self.game_over = False
        self.won = False

    def set_word(self, word):
        # Normalizar: Quitar tildes y poner mayúsculas
        self.target_word = ''.join(c for c in unicodedata.normalize('NFD', word)
                                   if unicodedata.category(c) != 'Mn').upper()
        # Inicializar display
        self.display_word = ["_" if c.isalpha() else c for c in self.target_word]
        self.lives = 6 # Reiniciar a 6 vidas
        self.guessed_letters = set()
        self.game_over = False
        self.won = False

    def guess(self, letter):
        if self.game_over or letter in self.guessed_letters:
            return False, "Repeated"

        self.guessed_letters.add(letter)
        
        if letter in self.target_word:
            for idx, char in enumerate(self.target_word):
                if char == letter:
                    self.display_word[idx] = letter
            
            if "_" not in self.display_word:
                self.won = True
                self.game_over = True
            return True, "Hit"
        else:
            self.lives -= 1
            if self.lives == 0:
                self.game_over = True
            return False, "Miss"

# --- 🖥️ INTERFAZ GRÁFICA ---
class HangmanApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NEON HANGMAN // AI EDITION")
        self.geometry("900x750")
        self.configure(fg_color=C_BG)
        self.resizable(False, False)

        self.game = GameModel()
        self.generated_options = []
        self.current_theme = ""

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        
        self.current_frame = None
        self.show_home_screen()

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()

    # --- PANTALLA 1: HOME ---
    def show_home_screen(self):
        self.clear_frame()
        # Reiniciamos variables clave
        self.generated_options = []
        self.current_theme = ""
        
        self.current_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.current_frame, text="H A N G M A N", font=("Impact", 60), text_color=C_ACCENT_1).pack(pady=(80, 10))
        ctk.CTkLabel(self.current_frame, text="PROTOCOL: GEMINI 1.5", font=("Consolas", 16), text_color=C_ACCENT_3).pack(pady=(0, 50))

        self.theme_entry = ctk.CTkEntry(
            self.current_frame, 
            placeholder_text="Ingresa Tema (Ej: Anime, Países...)",
            width=400, height=50,
            font=("Roboto", 14),
            border_color=C_ACCENT_1, fg_color=C_PANEL
        )
        self.theme_entry.pack(pady=10)
        self.theme_entry.bind("<Return>", lambda event: self.start_generation())

        self.btn_gen = ctk.CTkButton(
            self.current_frame, 
            text="GENERAR PALABRAS", 
            font=("Roboto", 14, "bold"),
            height=50, width=200,
            fg_color=C_ACCENT_1, hover_color="#00B8D4", text_color="black",
            command=self.start_generation
        )
        self.btn_gen.pack(pady=20)

        self.lbl_status = ctk.CTkLabel(self.current_frame, text="", font=("Consolas", 12), text_color=C_TEXT)
        self.lbl_status.pack(pady=10)

    # --- LÓGICA DE IA (CON PERSISTENCIA) ---
    def start_generation(self):
        theme = self.theme_entry.get().strip()
        if not theme:
            self.shake_window()
            return
        
        if not model:
            messagebox.showerror("Error", "API Key no configurada.")
            return

        self.current_theme = theme
        self.lbl_status.configure(text=f"ANALYZING HISTORY & GENERATING... [THEME: {theme.upper()}]", text_color=C_ACCENT_1)
        self.btn_gen.configure(state="disabled")
        
        # Cargar historial para este tema
        history = load_history()
        used_words = history.get(theme.lower(), [])
        
        threading.Thread(target=self.call_gemini, args=(theme, used_words), daemon=True).start()

    def call_gemini(self, theme, used_words):
        try:
            # Prompt con filtro de palabras usadas
            prompt = f"""
            Genera una lista JSON de 5 palabras o frases cortas relacionadas con: "{theme}".
            
            REGLAS ESTRICTAS:
            1. Palabras icónicas o fáciles.
            2. ¡IMPORTANTE! NO uses ninguna de estas palabras (ya se jugaron): {used_words}
            3. Solo devuelve el array JSON puro. Ejemplo: ["Palabra Uno", "Palabra Dos"]
            """
            
            response = model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            self.generated_options = json.loads(text)
            
            self.after(0, self.show_selection_screen)
            
        except Exception as e:
            print(e)
            self.after(0, lambda: self.handle_error("Error de conexión o filtro."))

    def handle_error(self, msg):
        self.lbl_status.configure(text=msg, text_color=C_ACCENT_2)
        self.btn_gen.configure(state="normal")

    # --- PANTALLA 2: SELECCIÓN ---
    def show_selection_screen(self):
        self.clear_frame()
        self.current_frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent") # Scroll por si acaso
        self.current_frame.pack(fill="both", expand=True, padx=40, pady=40)

        ctk.CTkLabel(self.current_frame, text="OBJETIVOS DETECTADOS", font=("Impact", 30), text_color=C_TEXT).pack(pady=(0, 20))
        ctk.CTkLabel(self.current_frame, text="Selecciona por longitud (Texto encriptado)", font=("Consolas", 12), text_color="gray").pack(pady=(0, 20))

        for word in self.generated_options:
            # Lógica de encriptado visual
            masked_text = ""
            for char in word:
                if char == " ": masked_text += "   " 
                else: masked_text += "█"
            
            ctk.CTkButton(
                self.current_frame,
                text=masked_text,
                font=("Arial", 24),
                fg_color=C_PANEL,
                border_color=C_ACCENT_1, border_width=1,
                hover_color="#1E1E1E", height=60,
                command=lambda w=word: self.start_game(w)
            ).pack(pady=10, fill="x", padx=50)

        ctk.CTkButton(self.current_frame, text="CANCELAR", fg_color=C_ACCENT_2, command=self.show_home_screen).pack(pady=30)

    # --- PANTALLA 3: JUEGO ---
    def start_game(self, word):
        # Guardamos la palabra en el historial para que no salga nunca más
        save_word_to_history(self.current_theme, word)
        
        self.game.set_word(word)
        self.show_game_screen()

    def show_game_screen(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True)

        self.current_frame.columnconfigure(0, weight=1)
        self.current_frame.columnconfigure(1, weight=1)
        self.current_frame.rowconfigure(0, weight=1)

        # PANEL IZQUIERDO (Canvas)
        left_panel = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self.canvas = tk.Canvas(left_panel, bg=C_PANEL, highlightthickness=0, height=450)
        self.canvas.pack(fill="x", pady=20)
        self.draw_gallows()

        self.lbl_lives = ctk.CTkLabel(left_panel, text="❤️❤️❤️❤️❤️❤️", font=("Arial", 30))
        self.lbl_lives.pack(pady=10)

        # PANEL DERECHO (Juego)
        right_panel = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.lbl_word = ctk.CTkLabel(right_panel, text=self.format_display_word(), font=("Consolas", 35, "bold"), text_color=C_ACCENT_1, wraplength=400)
        self.lbl_word.pack(pady=(50, 40))

        # Teclado
        keyboard_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        keyboard_frame.pack()
        
        alphabet = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
        self.key_buttons = {}
        row, col = 0, 0
        for char in alphabet:
            btn = ctk.CTkButton(
                keyboard_frame, text=char, width=45, height=45, font=("Roboto", 14, "bold"),
                fg_color=C_PANEL, border_width=1, border_color="gray",
                command=lambda c=char: self.process_guess(c)
            )
            btn.grid(row=row, column=col, padx=3, pady=3)
            self.key_buttons[char] = btn
            col += 1
            if col > 6: col = 0; row += 1

        ctk.CTkButton(right_panel, text="RENDIRSE", fg_color="transparent", border_width=1, border_color=C_ACCENT_2, text_color=C_ACCENT_2, command=self.show_home_screen).pack(side="bottom", pady=20)

    # --- LÓGICA DE JUEGO UI ---
    def format_display_word(self):
        return " ".join(self.game.display_word)

    def process_guess(self, char):
        if self.game.game_over: return
        btn = self.key_buttons[char]
        btn.configure(state="disabled", fg_color="#333333")

        success, msg = self.game.guess(char)

        if success:
            self.lbl_word.configure(text=self.format_display_word())
            btn.configure(border_color=C_ACCENT_1, text_color=C_ACCENT_1)
            if self.game.won: self.game_over_sequence(win=True)
        else:
            self.shake_window()
            btn.configure(border_color=C_ACCENT_2, text_color=C_ACCENT_2)
            self.update_lives_ui()
            self.draw_hangman_step()
            if self.game.game_over: self.game_over_sequence(win=False)

    def update_lives_ui(self):
        # 6 Vidas = 6 Corazones
        hearts = "❤️" * self.game.lives + "🖤" * (6 - self.game.lives)
        self.lbl_lives.configure(text=hearts)

    # --- DIBUJO DEL AHORCADO (6 PARTES) ---
    def draw_gallows(self):
        # Poste y cuerda
        c = C_TEXT
        self.canvas.create_line(50, 400, 150, 400, fill=c, width=3) # Base
        self.canvas.create_line(100, 400, 100, 50, fill=c, width=3) # Poste
        self.canvas.create_line(100, 50, 250, 50, fill=c, width=3)  # Brazo
        self.canvas.create_line(250, 50, 250, 80, fill=c, width=3)  # Cuerda

    def draw_hangman_step(self):
        lives = self.game.lives
        color = C_ACCENT_2 # Rojo Neon
        w = 4
        
        # Secuencia Inversa: 5=Cabeza, 4=Cuerpo, 3=B.Izq, 2=B.Der, 1=P.Izq, 0=P.Der/Fin
        if lives == 5: # Cabeza
            self.canvas.create_oval(220, 80, 280, 140, outline=color, width=w)
        elif lives == 4: # Cuerpo
            self.canvas.create_line(250, 140, 250, 260, fill=color, width=w)
        elif lives == 3: # Brazo Izquierdo
            self.canvas.create_line(250, 160, 210, 220, fill=color, width=w)
        elif lives == 2: # Brazo Derecho
            self.canvas.create_line(250, 160, 290, 220, fill=color, width=w)
        elif lives == 1: # Pierna Izquierda
            self.canvas.create_line(250, 260, 210, 330, fill=color, width=w)
        elif lives == 0: # Pierna Derecha + Ojos XX
            self.canvas.create_line(250, 260, 290, 330, fill=color, width=w)
            # Ojos de muerto
            self.canvas.create_line(235, 100, 245, 110, fill=color, width=2)
            self.canvas.create_line(245, 100, 235, 110, fill=color, width=2)
            self.canvas.create_line(255, 100, 265, 110, fill=color, width=2)
            self.canvas.create_line(265, 100, 255, 110, fill=color, width=2)

    # --- GAME OVER ---
    def game_over_sequence(self, win):
        if win:
            title = "MISIÓN CUMPLIDA"
            color = C_ACCENT_1
            msg = "Has descifrado la palabra clave."
        else:
            title = "SISTEMA COMPROMETIDO"
            color = C_ACCENT_2
            msg = f"La palabra era: {self.game.target_word}"
            
        overlay = ctk.CTkFrame(self, fg_color="#000000", corner_radius=20, border_width=2, border_color=color)
        overlay.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.45)
        
        ctk.CTkLabel(overlay, text=title, font=("Impact", 40), text_color=color).pack(pady=(40, 10))
        ctk.CTkLabel(overlay, text=msg, font=("Roboto", 18)).pack(pady=10)
        
        btn_frame = ctk.CTkFrame(overlay, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        # Botón Nuevo Tema que funciona de verdad
        ctk.CTkButton(btn_frame, text="NUEVO TEMA", fg_color=C_PANEL, border_color="white", border_width=1, command=self.show_home_screen).pack(side="left", padx=10)

    def shake_window(self):
        x = self.winfo_x()
        y = self.winfo_y()
        for i in range(0, 4):
            self.geometry(f"+{x+10}+{y}"); self.update(); time.sleep(0.02)
            self.geometry(f"+{x-10}+{y}"); self.update(); time.sleep(0.02)
        self.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    app = HangmanApp()
    app.mainloop()