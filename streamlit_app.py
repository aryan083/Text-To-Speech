import streamlit as st
import pyttsx3
import os
import logging
import threading
import time
from tempfile import NamedTemporaryFile
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSEngineManager:
    """Thread-safe TTS engine manager with resource cleanup"""
    _lock = threading.Lock()
    _engine: Optional[pyttsx3.Engine] = None
    
    @classmethod
    def get_engine(cls) -> pyttsx3.Engine:
        with cls._lock:
            if cls._engine is None:
                logger.info("Initializing new TTS engine")
                try:
                    cls._engine = pyttsx3.init()
                    # Configure default settings
                    cls._engine.setProperty('rate', 150)
                except Exception as e:
                    logger.error(f"Failed to initialize TTS engine: {str(e)}")
                    raise RuntimeError("Could not initialize TTS engine") from e
            return cls._engine
    
    @classmethod
    def shutdown(cls):
        with cls._lock:
            if cls._engine is not None:
                try:
                    logger.info("Shutting down TTS engine")
                    cls._engine.stop()
                    del cls._engine
                except Exception as e:
                    logger.error(f"Error during engine shutdown: {str(e)}")
                finally:
                    cls._engine = None

def configure_page():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title='Text to Speech Converter',
        page_icon="🔊",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    st.title("Text to Speech Converter")
    st.markdown("---")

def initialize_state():
    """Initialize session state variables"""
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None

def get_voice_settings(engine: pyttsx3.Engine) -> tuple:
    """Get available voices and validate selection"""
    voices = engine.getProperty('voices')
    if not voices:
        raise RuntimeError("No TTS voices available on the system")
    
    voice_labels = ['Default']
    if len(voices) > 1:
        voice_labels.extend(['Male', 'Female'] if len(voices) >= 2 else ['Alternative'])
    
    selected_voice = st.radio("Voice Type", voice_labels)
    return voices[0 if selected_voice == 'Default' else 1]

def generate_audio(text: str, speed: int, voice) -> Optional[str]:
    """Generate audio file from text with error handling"""
    engine = TTSEngineManager.get_engine()
    try:
        engine.setProperty('rate', speed)
        engine.setProperty('voice', voice.id)
        
        with NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
            temp_path = tmpfile.name
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            
        logger.info(f"Generated audio file: {temp_path}")
        return temp_path
        
    except Exception as e:
        logger.error(f"Audio generation failed: {str(e)}")
        st.error(f"Failed to generate audio: {str(e)}")
        return None

def cleanup_resources():
    """Cleanup temporary files and engine resources"""
    if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
        try:
            os.remove(st.session_state.audio_file)
            logger.info(f"Removed temporary file: {st.session_state.audio_file}")
        except Exception as e:
            logger.error(f"Error removing temp file: {str(e)}")
    TTSEngineManager.shutdown()

def main_interface():
    """Main application interface"""
    text_input = st.text_area(
        "Enter text to convert:",
        height=200,
        placeholder="Type or paste your text here..."
    )
    
    speed_setting = st.slider(
        "Speech Speed (words per minute)",
        min_value=50,
        max_value=300,
        value=175,
        step=25
    )
    
    try:
        engine = TTSEngineManager.get_engine()
        selected_voice = get_voice_settings(engine)
    except RuntimeError as e:
        st.error(str(e))
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Preview Speech", disabled=st.session_state.processing):
            if not text_input.strip():
                st.warning("Please enter some text to convert")
                return
            
            st.session_state.processing = True
            try:
                engine.say(text_input)
                engine.runAndWait()
            except Exception as e:
                st.error(f"Speech preview failed: {str(e)}")
            finally:
                st.session_state.processing = False
    
    with col2:
        if st.button("Generate Audio File", disabled=st.session_state.processing):
            if not text_input.strip():
                st.warning("Please enter some text to convert")
                return
            
            st.session_state.processing = True
            try:
                audio_path = generate_audio(text_input, speed_setting, selected_voice)
                if audio_path:
                    st.session_state.audio_file = audio_path
                    st.success("Audio file generated successfully!")
            finally:
                st.session_state.processing = False

    if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
        st.markdown("---")
        st.subheader("Download Audio")
        with open(st.session_state.audio_file, "rb") as f:
            st.download_button(
                label="Download WAV File",
                data=f,
                file_name="generated_speech.wav",
                mime="audio/wav"
            )

def main():
    configure_page()
    initialize_state()
    
    try:
        main_interface()
    finally:
        cleanup_resources()

if __name__ == "__main__":
    main()