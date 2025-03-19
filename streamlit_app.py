import streamlit as st
import pyttsx3
import base64
import threading
import time
import logging
import os
from queue import Queue

# Configure logging
logging.basicConfig(level=logging.INFO)

# TTS Engine Manager
class TTSEngine:
    _lock = threading.Lock()
    _instance = None

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                logging.info("Initializing new TTS engine instance")
                cls._instance = pyttsx3.init()
            return cls._instance

    @classmethod
    def cleanup(cls, engine):
        with cls._lock:
            if engine:
                try:
                    logging.info("Stopping TTS engine")
                    engine.stop()
                    if engine == cls._instance:
                        cls._instance = None
                        logging.info("TTS engine instance cleared")
                except Exception as e:
                    logging.error(f"Error during engine cleanup: {str(e)}")
                    pass

# Streamlit app configuration
st.set_page_config(page_title='Text to Speech Web App', layout='wide')

# Session state initialization
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'temp_files' not in st.session_state:
    st.session_state.temp_files = []

# Cleanup function for temporary files
def cleanup_temp_files():
    for file in st.session_state.temp_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                logging.info(f"Cleaned up temporary file: {file}")
        except Exception as e:
            logging.error(f"Error cleaning up file {file}: {str(e)}")
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

# Audio controls
def convert_and_play():
    engine = None
    try:
        st.session_state.processing = True
        engine = TTSEngine.get_instance()
        if not text.strip():
            st.error('Please enter some text to convert')
            return
        engine.setProperty('rate', speed)
        voices = engine.getProperty('voices')
        if not voices:
            st.error('No voices available in the system')
            return
        engine.setProperty('voice', voices[0 if voice_type == 'Male' else 1].id)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        st.error(f'Speech generation error: {str(e)}')
    finally:
        if engine:
            TTSEngine.cleanup(engine)
        st.session_state.processing = False

# Audio file generation
def generate_audio_file():
    engine = None
    try:
        st.session_state.processing = True
        logging.info("Starting audio file generation")
        engine = TTSEngine.get_instance()
        if not text.strip():
            st.error('Please enter some text to convert')
            return None
        logging.info(f"Configuring TTS engine with speed {speed} and voice type {voice_type}")
        engine.setProperty('rate', speed)
        voices = engine.getProperty('voices')
        if not voices:
            st.error('No voices available in the system')
            return None
        engine.setProperty('voice', voices[0 if voice_type == 'Male' else 1].id)
        filename = f"tts_output_{int(time.time())}.wav"
        logging.info(f"Saving audio to file: {filename}")
        engine.save_to_file(text, filename)
        engine.runAndWait()
        st.session_state.temp_files.append(filename)
        logging.info("Audio file generation completed successfully")
        return filename
    except Exception as e:
        logging.error(f"Audio generation failed: {str(e)}")
        st.error(f'Audio save failed: {str(e)}')
        return None
    finally:
        if engine:
            TTSEngine.cleanup(engine)
        st.session_state.processing = False

# Button columns
btn_col1, btn_col2, _ = st.columns([1,1,2])

with btn_col1:
    if st.button('Convert & Play', disabled=st.session_state.processing):
        threading.Thread(target=convert_and_play, daemon=True).start()

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

# Cleanup on session end and refresh
st.session_state.on_close = TTSEngine.cleanup
cleanup_temp_files()