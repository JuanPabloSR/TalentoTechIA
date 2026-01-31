import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import speech_recognition as sr
import threading
import time
import math
import struct 
import pyaudio 
from docx import Document
from docx.shared import Pt
from fpdf import FPDF

# --- CONFIGURACIÓN DE COLORES JJK ---
COLOR_FONDO = "#050505"       
COLOR_TEXTO = "#e0e0e0"
COLOR_GOJO = "#a020f0"        # Púrpura
COLOR_SUKUNA = "#ff0000"      # Rojo Sangre (Más brillante para que destaque)
COLOR_ENERGIA = "#00ffff"     # Azul cian
COLOR_PANEL = "#1c1c1c"       

class JujutsuVoiceApp: 
    def __init__(self, root):
        self.root = root
        self.root.title("Jujutsu Kaisen: Culling Game Recorder [Grado Especial]")
        self.root.geometry("650x780")
        self.root.configure(bg=COLOR_FONDO)

        # Variables
        self.is_recording = False
        self.stop_event = threading.Event()
        self.recognizer = sr.Recognizer()
        self.full_text = ""
        self.start_time = 0
        
        # Audio Stream
        self.p = pyaudio.PyAudio()
        self.stream = None

        # --- ESTILOS ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=COLOR_PANEL, background=COLOR_GOJO, foreground="white", arrowcolor="white")

        # --- UI ---
        header_frame = tk.Frame(root, bg=COLOR_FONDO)
        header_frame.pack(pady=20)
        
        tk.Label(header_frame, text="⚡ EXTENSIÓN DE DOMINIO ⚡", font=("Impact", 22), bg=COLOR_FONDO, fg=COLOR_GOJO).pack()
        tk.Label(header_frame, text="Herramienta de Transcripción Maldita", font=("Consolas", 10), bg=COLOR_FONDO, fg="gray").pack()

        lbl_select = tk.Label(root, text="Selecciona el Pacto (Formato):", font=("Arial", 10, "bold"), bg=COLOR_FONDO, fg="#cfd8dc")
        lbl_select.pack(pady=(10, 0))

        self.type_doc = ttk.Combobox(root, values=["📜 Informe (Carta)", "📊 Clasificación (Evaluación)", "📝 Voto Vinculante (Formulario)", "🧠 Resumen del Incidente"], state="readonly", font=("Arial", 11))
        self.type_doc.current(0)
        self.type_doc.pack(pady=5, ipadx=10)

        # CANVAS DE ENERGÍA (Visualizador)
        self.canvas = tk.Canvas(root, width=600, height=40, bg=COLOR_PANEL, highlightthickness=1, highlightbackground="#333")
        self.canvas.pack(pady=10)
        
        self.center_x = 300
        self.energy_bar = self.canvas.create_rectangle(self.center_x, 5, self.center_x, 35, fill=COLOR_ENERGIA, outline="")

        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=15, font=("Consolas", 11), bg="#121212", fg="#00ff00", insertbackground="white", bd=0)
        self.text_area.pack(pady=10, padx=20)
        self.text_area.config(highlightbackground=COLOR_GOJO, highlightthickness=2)

        frame_controls = tk.Frame(root, bg=COLOR_FONDO)
        frame_controls.pack(pady=10)

        self.btn_record = tk.Button(frame_controls, text="🤞 INVOCAR (Grabar)", command=self.toggle_recording, bg=COLOR_GOJO, fg="white", font=("Arial", 11, "bold"), width=20, relief="flat")
        self.btn_record.pack(side=tk.LEFT, padx=10)

        self.btn_reset = tk.Button(frame_controls, text="🩸 PURIFICAR (Borrar)", command=self.reset_recording, bg="#8a0303", fg="white", font=("Arial", 11, "bold"), width=18, relief="flat")
        self.btn_reset.pack(side=tk.LEFT, padx=10)

        self.btn_ai = tk.Button(root, text="🧠 INVOCAR A MAHORAGA (Adaptar Texto con IA)", command=self.simular_ia_improve, bg="#006064", fg="white", font=("Arial", 10, "bold"), relief="flat", cursor="hand2")
        self.btn_ai.pack(pady=5, fill=tk.X, padx=50)

        frame_save = tk.Frame(root, bg=COLOR_FONDO)
        frame_save.pack(pady=10)
        tk.Button(frame_save, text="💾 Sellar WORD", command=lambda: self.save_file("word"), bg="#283593", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(frame_save, text="💾 Sellar PDF", command=lambda: self.save_file("pdf"), bg="#c62828", fg="white").pack(side=tk.LEFT, padx=5)

        self.status_lbl = tk.Label(root, text="Esperando conjuro...", bg=COLOR_PANEL, fg="white", anchor=tk.W)
        self.status_lbl.pack(side=tk.BOTTOM, fill=tk.X)

    # --- AQUÍ ESTÁ EL CAMBIO DE SENSIBILIDAD ---
    def audio_visualizer_loop(self):
        try:
            self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
            
            while not self.stop_event.is_set():
                try:
                    data = self.stream.read(1024, exception_on_overflow=False)
                    
                    # Calcular volumen (RMS)
                    count = len(data) // 2
                    format_str = "%dh" % count
                    shorts = struct.unpack(format_str, data)
                    sum_squares = sum(s**2 for s in shorts)
                    rms = math.sqrt(sum_squares / count)
                    
                    # --- AJUSTE MAESTRO DE SENSIBILIDAD ---
                    # Antes dividíamos por 50. Ahora por 5.
                    # Esto hace que la barra crezca mucho más rápido con menos ruido.
                    sensibilidad = 5 
                    ancho_barra = min((rms / sensibilidad), 300) 

                    self.update_canvas(ancho_barra)
                    
                except Exception:
                    break
        except Exception as e:
            print(f"Error visualizador: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()

    def update_canvas(self, val):
        try:
            x0 = self.center_x - val
            x1 = self.center_x + val
            self.canvas.coords(self.energy_bar, x0, 5, x1, 35)
            
            # Umbrales ajustados para que sea fácil llegar al rojo
            if val < 80:
                color = COLOR_ENERGIA # Azul (Voz baja)
            elif val < 200:
                color = COLOR_GOJO    # Púrpura (Voz normal)
            else:
                color = COLOR_SUKUNA  # Rojo (Voz fuerte)
                
            self.canvas.itemconfig(self.energy_bar, fill=color)
        except: pass

    # --- RESTO DEL CÓDIGO IGUAL ---
    def simular_ia_improve(self):
        texto_actual = self.text_area.get("1.0", tk.END).strip()
        if not texto_actual:
            messagebox.showwarning("Vacío", "No hay texto.")
            return
        messagebox.showinfo("Mahoraga", "Adaptándose al texto...")
        texto_mejorado = texto_actual.capitalize().replace(" i ", " y ") + "."
        self.text_area.insert(tk.END, "\n\n--- 👹 ADAPTACIÓN COMPLETADA ---\n" + texto_mejorado)

    def toggle_recording(self):
        if not self.is_recording: self.start_recording()
        else: self.stop_recording()
    
    def start_recording(self):
        self.is_recording = True
        self.stop_event.clear()
        self.btn_record.config(text="✋ ROMPER DOMINIO", bg="#ff9100", fg="black")
        self.status_lbl.config(text="🔴 GRABANDO...")
        self.start_time = time.time()
        threading.Thread(target=self.record_loop, daemon=True).start()
        threading.Thread(target=self.audio_visualizer_loop, daemon=True).start()
    
    def stop_recording(self):
        self.is_recording = False
        self.stop_event.set()
        self.btn_record.config(text="🤞 INVOCAR (Grabar)", bg=COLOR_GOJO, fg="white")
        self.status_lbl.config(text="Dominio cerrado.")
        self.canvas.coords(self.energy_bar, self.center_x, 5, self.center_x, 35)

    def reset_recording(self):
        if self.is_recording: self.stop_recording()
        if messagebox.askyesno("Técnica Inversa", "¿Borrar todo?"):
            self.full_text = ""
            self.text_area.delete("1.0", tk.END)

    def record_loop(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            while not self.stop_event.is_set():
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    try:
                        text = self.recognizer.recognize_google(audio, language="es-ES")
                        self.full_text += text + " "
                        self.text_area.insert(tk.END, text + " ")
                        self.text_area.see(tk.END)
                        if time.time() - self.start_time > 10:
                            self.root.after(0, self.ask_continue)
                            break
                    except sr.UnknownValueError: pass
                except sr.WaitTimeoutError: pass
                except Exception: break

    def ask_continue(self):
        self.stop_recording()
        if messagebox.askyesno("Límite", "¿Continuar?"): self.start_recording()

    def save_file(self, format):
        content = self.text_area.get("1.0", tk.END).strip()
        type_doc = self.type_doc.get().split(" ")[1].upper() 
        if not content: return
        if format == "word":
            f_name = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word", "*.docx")])
            if f_name:
                doc = Document()
                doc.add_heading(f"--- {type_doc} ---", 0)
                doc.add_paragraph(content)
                doc.save(f_name)
                messagebox.showinfo("Hecho", "Word guardado.")
        elif format == "pdf":
            f_name = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if f_name:
                try:
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=10)
                    pdf.cell(0, 10, f"--- {type_doc} ---", ln=1, align='C')
                    pdf.multi_cell(0, 5, content.encode('latin-1', 'replace').decode('latin-1'))
                    pdf.output(f_name)
                    messagebox.showinfo("Hecho", "PDF guardado.")
                except Exception as e: messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = JujutsuVoiceApp(root)
    root.mainloop()