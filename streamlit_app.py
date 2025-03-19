import streamlit as st
import pyttsx3
import threading
import time
import logging
import os
from streamlit.runtime.scriptrunner import add_script_run_ctx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TTS Engine Manager with Streamlit-cloud fixes
class TTSEngine:
    _lock = threading.Lock()
    _instance = None

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                try:
                    logger.info("Initializing TTS engine")
                    cls._instance = pyttsx3.init()
                except Exception as e:
                    logger.error(f"TTS init failed: {str(e)}")
                    st.error("Failed to initialize speech engine. Check system dependencies.")
                    raise
            return cls._instance

    @classmethod
    def cleanup(cls):
        with cls._lock:
            if cls._instance:
                try:
                    logger.info("Cleaning up TTS engine")
                    cls._instance.stop()
                    del cls._instance
                except Exception as e:
                    logger.error(f"Cleanup error: {str(e)}")
                finally:
                    cls._instance = None

# Streamlit app configuration
st.set_page_config(page_title='Text to Speech', layout='wide')

# Session state initialization
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'audio_file' not in st.session_state:
    st.session_state.audio_file = None

def convert_and_play():
    """Thread-safe audio conversion with proper context"""
    engine = None
    try:
        engine = TTSEngine.get_instance()
        if not st.session_state.text_input.strip():
            st.error("Please enter text to convert")
            return

        engine.setProperty('rate', st.session_state.speed)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0 if st.session_state.voice_type == 'Male' else 1].id)
        
        engine.say(st.session_state.text_input)
        engine.runAndWait()

    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        st.error(f"Speech conversion failed: {str(e)}")
    finally:
        if engine:
            TTSEngine.cleanup()
        st.session_state.processing = False

def main_app():
    st.title("Text to Speech Converter")
    
    # Store settings in session state
    st.session_state.text_input = st.text_area("Input Text", height=150)
    st.session_state.speed = st.slider("Speech Speed", 50, 300, 175)
    st.session_state.voice_type = st.radio("Voice Type", ['Male', 'Female'])
    
    # Conversion button with context wrapper
    if st.button("Convert & Play", disabled=st.session_state.processing):
        st.session_state.processing = True
        try:
            # Create thread with proper Streamlit context
            thread = threading.Thread(target=convert_and_play)
            add_script_run_ctx(thread)
            thread.start()
        except Exception as e:
            st.error(f"Failed to start conversion: {str(e)}")
            st.session_state.processing = False

    # Status indicator
    if st.session_state.processing:
        st.warning("Processing audio...")
    else:
        st.success("Ready for conversion")

if __name__ == "__main__":
    main_app()
    # Cleanup on app exit
    TTSEngine.cleanup()