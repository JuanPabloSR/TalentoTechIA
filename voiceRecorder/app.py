
import threading
import time
from tkinter import scrolledtext


class DictadoApp: 
    def __init__(self):
        self.root = root
        self.root.title("Asistente de Dictado por Voz")
        self.root.geometry("500x600")

        # Enviroment
        self.is_recording = False
        self.stop_event = threading.Event()
        self.recognizer = sr.Recognizer()
        self.full_text = ""
        self.start_time = 0

        # UI
        # Select type document
        lbl_type = tk.label(root, text="Seleccione el tipo de documento", font=("Arial", 12))
        lbl_type.pack(pady=10)

        self.type_doc = ttk.Combobox(root, values=["Carta", "Evaluacion", "Formulario", "Resumen Ejecutivo"], state="readonly")
        self.type_doc.current(0)
        self.type_doc.pack(pady=5)

        # Text area
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20, font=("Arial", 10))
        self.text_area.pack(pady=10, padx=10)

        # Buttons
        frame_btn = tk.Frame(root)
        frame_btn.pack(pady=10)

        self.btn_recording = tk.Button(frame_btn, text="Iniciar Grabación", command=self.toggle_recording, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.btn_recording.pack(side=tk.LEFT, padx=10)

        self.btn_save_word = tk.Button(frame_btn, text="💾 Word", command=lambda: self.guardar_archivo("word"), bg="#2196F3", fg="white")
        self.btn_save_word.pack(side=tk.LEFT, padx=5)

        self.btn_save_pdf = tk.Button(frame_btn, text="💾 PDF", command=lambda: self.guardar_archivo("pdf"), bg="#f44336", fg="white")
        self.btn_save_pdf.pack(side=tk.LEFT, padx=5)
        
        self.status_lbl = tk.Label(root, text="Listo para dictar...", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_lbl.pack(side=tk.BOTTOM, fill=tk.X)
        
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.is_recording = True
        self.stop_event.clear()
        self.btn_recording.config(text="⏹ Detener Grabación", bg="#FF9800")
        self.start_time = time.time()
        
        threading.Thread(target=self.record_loop, daemon=True).start()
    
    def stop_recording(self):
        self.is_recording = False
        self.stop_event.set()
        self.btn_recording.config(text="Iniciar Dictado", bg="#4CAF50")
        self.status_lbl.config(text="Pausado")
        
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
                        
                        elapsed_time = time.time() - self.start_time
                        if elapsed_time > 10:
                            self.root.after(0, self.ask_continue)
                            break
                    except sr.UnknownValueError:
                        pass
                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    print(f"Error: {e}")
                    break
                