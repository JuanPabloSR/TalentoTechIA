import streamlit as st
import google.generativeai as genai
import os
import time
import json
from moviepy.editor import VideoFileClip
from dotenv import load_dotenv
from pathlib import Path

# --- CONFIGURACIÓN ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

MODEL_NAME = "gemini-2.5-flash" 

if not api_key:
    st.error("❌ Falta la API Key en el archivo .env")
    st.stop()

genai.configure(api_key=api_key)

st.set_page_config(page_title="Asistente Legal", page_icon="⚖️", layout="wide")

# Carpetas y Archivos
TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)
HISTORY_FILE = "history.json"
PROMPTS_FILE = "prompts.json"

DEFAULT_PROMPTS = {
    "Resumen General": "Haz un resumen ejecutivo de la audiencia: Partes involucradas, motivo de la audiencia y estado actual del proceso.",
    "Práctica de Pruebas (Alegatos)": """Analiza el audio de la audiencia judicial y EXTRAE lo probatoriamente útil para redactar alegatos de conclusión (o informe de audiencia).
    Entrega en español, formal, con marcas de tiempo (min:seg) para cada punto relevante.

    ESTRUCTURA OBLIGATORIA DEL INFORME:
    1) Resumen ejecutivo (máx. 8 líneas): tipo de proceso, pretensiones, hechos debatidos y propósito de la audiencia.
    2) Argumentos por parte (5–8 bullets por cada una): qué afirma, qué busca probar y en qué se apoya (con min:seg).
    3) Prueba practicada (OBLIGATORIO Y DETALLADO):
       - Testimonios: por cada testigo, 6–10 líneas con (i) calidad/rol, (ii) hechos clave que confirma, (iii) contradicciones o admisiones, (iv) daños/perjuicios si aplica, (v) 1 cita corta textual entre comillas, todo con min:seg.
       - Documentos: listar los documentos mencionados y para qué sirven (min:seg).
    4) Decisiones del juez y estado del proceso: órdenes, términos, cierres de etapa, recursos (min:seg).
    5) Extracto para alegatos (Entregable Final): 3–5 párrafos redactados profesionalmente "listos para copiar y pegar" que conecten lo probado -> la norma/tesis del caso -> la petición.""",
    "Cronología": "Crea una lista cronológica con MARCAS DE TIEMPO (Minuto:Segundo) de los eventos cruciales, intervenciones y decisiones.",
    "Sentencia/Decisión": "Extrae exclusivamente la decisión final del juez (el fallo), los argumentos que usó y si hubo apelaciones."
}

# --- MEMORIA DE SESIÓN ---
if 'current_audio_path' not in st.session_state:
    st.session_state['current_audio_path'] = None
if 'last_analysis' not in st.session_state:
    st.session_state['last_analysis'] = ""
if 'file_id' not in st.session_state:
    st.session_state['file_id'] = None

# --- FUNCIONES ---

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_to_history(filename, analysis_preview):
    history = load_history()
    new_entry = {
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "filename": filename,
        "preview": analysis_preview[:150] + "..."
    }
    history.insert(0, new_entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[:20], f, ensure_ascii=False, indent=2)

def load_prompts():
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_PROMPTS, f, ensure_ascii=False, indent=2)
    return DEFAULT_PROMPTS

def save_prompts(prompts_dict):
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts_dict, f, ensure_ascii=False, indent=2)

if 'prompts' not in st.session_state:
    st.session_state['prompts'] = load_prompts()

def extract_audio(video_file, file_name_id):
    audio_path = TEMP_DIR / f"{file_name_id}.mp3"
    video_path = TEMP_DIR / f"{file_name_id}.mp4"
    
    if audio_path.exists():
        return str(audio_path)
    
    with open(video_path, "wb") as f:
        f.write(video_file.getbuffer())
    
    try:
        video = VideoFileClip(str(video_path))
        video.audio.write_audiofile(str(audio_path), bitrate="32k", logger=None)
        video.close()
        
        if os.path.exists(video_path):
            os.remove(video_path) 
            
        return str(audio_path)
    except Exception as e:
        st.error(f"Error extrayendo audio: {e}")
        return None

def analyze_audio(audio_path, prompt_text):
    model = genai.GenerativeModel(MODEL_NAME)
    
    system_instruction = """
    ACTÚA COMO UN ASISTENTE LEGAL EXPERTO.
    TU IDIOMA ES ESPAÑOL DE COLOMBIA.
    USA TERMINOLOGÍA JURÍDICA PRECISA, FORMAL Y CLARA.
    """
    
    final_prompt = f"{system_instruction}\n\nTAREA: {prompt_text}"

    try:
        myfile = genai.upload_file(audio_path)
        
        while myfile.state.name == "PROCESSING":
            time.sleep(1)
            myfile = genai.get_file(myfile.name)
        
        if myfile.state.name == "FAILED":
            return "Error: Google rechazó el archivo de audio."

        response = model.generate_content([myfile, final_prompt])
        return response.text
            
    except Exception as e:
        return f"Ocurrió un error técnico: {e}"

# --- INTERFAZ VISUAL ---

with st.sidebar:
    st.header("📂 Historial")
    history = load_history()
    if not history:
        st.caption("No hay análisis recientes.")
    for item in history:
        st.text(f"📅 {item['date']}")
        st.caption(f"📁 {item['filename']}")
        with st.expander("Ver inicio"):
            st.write(item['preview'])
        st.divider()

st.title("⚖️ Asistente de Audiencias")
st.markdown("Automatización de análisis jurídico con **Gemini 2.0 Flash**")

uploaded_file = st.file_uploader("Arrastra aquí el video de la audiencia (.mp4)", type=["mp4", "mov", "mkv"])

if uploaded_file:
    file_id = f"{uploaded_file.size}_{uploaded_file.name}".replace(" ", "_")
    
    if st.session_state['file_id'] != file_id:
        st.session_state['file_id'] = file_id
        st.session_state['current_audio_path'] = None
        st.session_state['last_analysis'] = ""
    
    if not st.session_state['current_audio_path']:
        if st.button("▶️ Iniciar Procesamiento del Video", type="primary"):
            with st.status("Procesando video...", expanded=True) as status:
                st.write("🔧 Extrayendo audio y comprimiendo...")
                path = extract_audio(uploaded_file, file_id)
                
                if path:
                    st.session_state['current_audio_path'] = path
                    status.update(label="¡Video procesado correctamente!", state="complete", expanded=False)
                    st.rerun()
                else:
                    status.update(label="Error en el procesamiento", state="error")
    
    else:
        st.success(f"✅ Archivo listo: {uploaded_file.name}")
        
        col_opts, col_actions = st.columns([2, 1])
        
        with col_opts:
            st.subheader("1. Configurar Análisis")
            
            nombres_prompts = list(st.session_state['prompts'].keys())
            option = st.selectbox("Selecciona el tipo de informe:", nombres_prompts)
            
            with st.expander("⚙️ Gestionar Prompts Personalizados"):
                tab1, tab2 = st.tabs(["Crear Nuevo", "Editar / Eliminar"])
                
                with tab1:
                    nuevo_nombre = st.text_input("Nombre del nuevo prompt:")
                    nuevo_texto = st.text_area("Instrucciones para la IA:", height=150)
                    if st.button("💾 Guardar Prompt"):
                        if nuevo_nombre and nuevo_texto:
                            st.session_state['prompts'][nuevo_nombre] = nuevo_texto
                            save_prompts(st.session_state['prompts'])
                            st.success("Prompt guardado exitosamente.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("Llena ambos campos para guardar.")

                with tab2:
                    prompt_a_editar = st.selectbox("Selecciona un prompt para modificar:", nombres_prompts, key="edit_select")
                    texto_actual = st.session_state['prompts'][prompt_a_editar]
                    
                    texto_modificado = st.text_area("Modifica las instrucciones:", value=texto_actual, height=150)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("🔄 Actualizar", use_container_width=True):
                            st.session_state['prompts'][prompt_a_editar] = texto_modificado
                            save_prompts(st.session_state['prompts'])
                            st.success("Actualizado.")
                            time.sleep(1)
                            st.rerun()
                            
                    with col_btn2:
                        if st.button("🗑️ Eliminar", type="primary", use_container_width=True):
                            if len(st.session_state['prompts']) > 1:
                                del st.session_state['prompts'][prompt_a_editar]
                                save_prompts(st.session_state['prompts'])
                                st.error("Prompt eliminado.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.warning("No puedes eliminar el último prompt.")

            st.markdown("---")
            with open(st.session_state['current_audio_path'], "rb") as audio_file:
                st.download_button(
                    label="⬇️ Descargar Audio (MP3)",
                    data=audio_file,
                    file_name=f"Audio_{st.session_state['file_id']}.mp3",
                    mime="audio/mpeg"
                )

        with col_actions:
            st.subheader("2. Ejecutar")
            if st.button("✨ Generar Informe con IA", type="primary"):
                with st.status("Consultando a la Inteligencia Artificial...", expanded=True) as status:
                    st.write("☁️ Subiendo audio a la nube de Google...")
                    time.sleep(1) 
                    
                    st.write("🧠 Analizando testimonios y argumentos...")
                    texto_del_prompt = st.session_state['prompts'][option]
                    result = analyze_audio(st.session_state['current_audio_path'], texto_del_prompt)
                    
                    if result and "Error" not in result:
                        st.session_state['last_analysis'] = result
                        save_to_history(uploaded_file.name, result)
                        status.update(label="¡Análisis Finalizado!", state="complete", expanded=False)
                    else:
                        st.error(result)
                        status.update(label="Fallo en el análisis", state="error")

if st.session_state['last_analysis']:
    st.markdown("---")
    st.subheader("📋 Informe Generado")
    st.markdown(st.session_state['last_analysis'])
    
    st.download_button(
        "📥 Descargar Informe (.txt)", 
        st.session_state['last_analysis'], 
        file_name=f"Analisis_{st.session_state['file_id']}.txt"
    )