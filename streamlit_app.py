import streamlit as st
import pyttsx3
import base64
import threading
import time
import logging
import os
from queue import Queue
from streamlit.runtime.scriptrunner import add_script_run_ctx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TTS Engine Manager with enhanced error handling
class TTSEngine:
    _lock = threading.Lock()
    _instance = None
    _initialization_attempted = False

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None and not cls._initialization_attempted:
                try:
                    logger.info("Initializing new TTS engine instance")
                    cls._instance = pyttsx3.init()
                    cls._initialization_attempted = True
                except Exception as e:
                    logger.error(f"TTS engine initialization failed: {str(e)}")
                    cls._instance = None
            return cls._instance

    @classmethod
    def cleanup(cls, engine):
        with cls._lock:
            if engine and engine == cls._instance:
                try:
                    logger.info("Stopping TTS engine")
                    engine.stop()
                    del engine
                    cls._instance = None
                except Exception as e:
                    logger.error(f"Error during engine cleanup: {str(e)}")

# Streamlit app configuration
st.set_page_config(page_title='Text to Speech Web App', layout='wide')

# Session state initialization
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'temp_files' not in st.session_state:
    st.session_state.temp_files = []
if 'lock' not in st.session_state:
    st.session_state.lock = threading.Lock()

# Cleanup function for temporary files
def cleanup_temp_files():
    for file in st.session_state.temp_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                logger.info(f"Cleaned up temporary file: {file}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file}: {str(e)}")
    st.session_state.temp_files = []

# App layout
st.title('Text to Speech Web App')

# Text input
text = st.text_area('Enter text to convert:', height=200)

# Settings columns
col1, col2 = st.columns(2)

with col1:
    speed = st.slider('Speech Speed', 50, 200, 100)
    
with col2:
    voice_type = st.radio('Voice Type', ['Male', 'Female'])

# Thread-safe audio conversion
def convert_and_play():
    engine = None
    try:
        engine = TTSEngine.get_instance()
        if not engine:
            raise RuntimeError("TTS engine initialization failed")
            
        if not text.strip():
            with st.session_state.lock:
                st.error('Please enter some text to convert')
            return

        engine.setProperty('rate', speed)
        voices = engine.getProperty('voices')
        
        if not voices:
            with st.session_state.lock:
                st.error('No voices available in the system')
            return

        engine.setProperty('voice', voices[0 if voice_type == 'Male' else 1].id)
        engine.say(text)
        engine.runAndWait()
        
    except Exception as e:
        with st.session_state.lock:
            st.error(f'Speech generation error: {str(e)}')
    finally:
        if engine:
            TTSEngine.cleanup(engine)
        with st.session_state.lock:
            st.session_state.processing = False

# Audio file generation with proper context
def generate_audio_file():
    engine = None
    try:
        with st.session_state.lock:
            st.session_state.processing = True
            
        engine = TTSEngine.get_instance()
        if not engine:
            raise RuntimeError("TTS engine initialization failed")

        if not text.strip():
            with st.session_state.lock:
                st.error('Please enter some text to convert')
            return None

        engine.setProperty('rate', speed)
        voices = engine.getProperty('voices')
        
        if not voices:
            with st.session_state.lock:
                st.error('No voices available in the system')
            return None

        engine.setProperty('voice', voices[0 if voice_type == 'Male' else 1].id)
        filename = f"tts_output_{int(time.time())}.wav"
        
        engine.save_to_file(text, filename)
        engine.runAndWait()
        
        with st.session_state.lock:
            st.session_state.temp_files.append(filename)
            
        return filename
        
    except Exception as e:
        with st.session_state.lock:
            st.error(f'Audio save failed: {str(e)}')
        return None
    finally:
        if engine:
            TTSEngine.cleanup(engine)
        with st.session_state.lock:
            st.session_state.processing = False

# Button columns with proper thread handling
btn_col1, btn_col2, _ = st.columns([1,1,2])

with btn_col1:
    if st.button('Convert & Play', disabled=st.session_state.processing):
        thread = threading.Thread(target=convert_and_play, daemon=True)
        add_script_run_ctx(thread)
        thread.start()

with btn_col2:
    if st.button('Save as Audio', disabled=st.session_state.processing):
        audio_file = generate_audio_file()
        if audio_file:
            with open(audio_file, "rb") as f:
                bytes = f.read()
                st.download_button(
                    label="Download Audio",
                    data=bytes,
                    file_name=audio_file,
                    mime="audio/wav",
                    on_click=lambda: cleanup_temp_files()
                )

# Status indicator
if st.session_state.processing:
    st.warning('Audio processing in progress...')
else:
    st.success('Ready for new conversion')

# Cleanup on session end
def on_close():
    TTSEngine.cleanup()
    cleanup_temp_files()

st.session_state.on_close = on_close