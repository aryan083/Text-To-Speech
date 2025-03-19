import streamlit as st
import pyttsx3
import threading
import logging
from streamlit.runtime.scriptrunner import add_script_run_ctx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-safe TTS Engine Manager
class TTSEngine:
    _lock = threading.Lock()
    _instance = None
    
    @classmethod
    def get_engine(cls):
        with cls._lock:
            if cls._instance is None:
                try:
                    logger.info("Initializing TTS engine")
                    cls._instance = pyttsx3.init()
                except Exception as e:
                    logger.error(f"TTS initialization failed: {str(e)}")
                    st.error("Speech engine initialization failed. Please try again.")
                    cls._instance = None
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
st.set_page_config(page_title="Text to Speech", layout="wide")

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False

def safe_convert():
    """Thread-safe conversion function with proper Streamlit context"""
    try:
        engine = TTSEngine.get_engine()
        if not engine:
            st.error("Speech engine not available")
            return
            
        text = st.session_state.text_input
        if not text.strip():
            st.error("Please enter some text")
            return
            
        engine.setProperty('rate', st.session_state.speed)
        voices = engine.getProperty('voices')
        voice_index = 0 if st.session_state.voice_type == 'Male' else 1
        if len(voices) > voice_index:
            engine.setProperty('voice', voices[voice_index].id)
            
        engine.say(text)
        engine.runAndWait()
        
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        st.error(f"Conversion failed: {str(e)}")
    finally:
        TTSEngine.cleanup()
        st.session_state.processing = False

# Main UI
st.title("Text to Speech Converter")

# Input controls
st.text_area("Input Text", key="text_input", height=150)
st.slider("Speech Speed", 50, 300, 175, key="speed")
st.radio("Voice Type", ['Male', 'Female'], key="voice_type")

# Conversion button
if st.button("Convert to Speech", disabled=st.session_state.processing):
    st.session_state.processing = True
    try:
        # Create and start thread with proper context
        thread = threading.Thread(target=safe_convert)
        add_script_run_ctx(thread)
        thread.start()
    except Exception as e:
        st.error(f"Failed to start conversion: {str(e)}")
        st.session_state.processing = False

# Status indicator
if st.session_state.processing:
    st.warning("Processing... (This may take a moment)")
else:
    st.success("Ready for input")

# Cleanup on app exit
TTSEngine.cleanup()