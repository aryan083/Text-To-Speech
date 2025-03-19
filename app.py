from flask import Flask, render_template, request, send_file, jsonify
import pyttsx3
import os
import tempfile
import threading
import logging
from werkzeug.serving import WSGIRequestHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

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
    def cleanup(cls):
        with cls._lock:
            if cls._instance:
                try:
                    logger.info("Stopping TTS engine")
                    cls._instance.stop()
                    cls._instance = None
                except Exception as e:
                    logger.error(f"Error during engine cleanup: {str(e)}")

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Template rendering error: {str(e)}")
        # Check if template exists
        template_path = os.path.join(app.template_folder, 'index.html')
        if not os.path.exists(template_path):
            logger.error(f"Template not found at {template_path}")
            return jsonify({'error': 'Template not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/convert-play', methods=['POST'])
def convert_play():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        speed = int(data.get('speed', 100))
        voice_type = data.get('voice_type', 'Male')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        engine = TTSEngine.get_instance()
        if not engine:
            return jsonify({'error': 'TTS engine initialization failed'}), 500

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_filename = temp_file.name
        temp_file.close()

        try:
            # Configure engine
            engine.setProperty('rate', speed)
            voices = engine.getProperty('voices')
            voice_index = 0 if voice_type == 'Male' else 1
            if voices and len(voices) > voice_index:
                engine.setProperty('voice', voices[voice_index].id)

            # Generate audio file
            engine.save_to_file(text, temp_filename)
            engine.runAndWait()

            # Send file
            return send_file(
                temp_filename,
                mimetype='audio/wav',
                as_attachment=True,
                download_name='tts_output.wav'
            )
        finally:
            # Cleanup
            try:
                os.unlink(temp_filename)
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")

    except Exception as e:
        logger.error(f"Error in convert_play: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        speed = int(data.get('speed', 100))
        voice_type = data.get('voice_type', 'Male')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        engine = TTSEngine.get_instance()
        if not engine:
            return jsonify({'error': 'TTS engine initialization failed'}), 500

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_filename = temp_file.name
        temp_file.close()

        try:
            # Configure engine
            engine.setProperty('rate', speed)
            voices = engine.getProperty('voices')
            voice_index = 0 if voice_type == 'Male' else 1
            if voices and len(voices) > voice_index:
                engine.setProperty('voice', voices[voice_index].id)

            # Generate audio file
            engine.save_to_file(text, temp_filename)
            engine.runAndWait()

            # Send file
            return send_file(
                temp_filename,
                mimetype='audio/wav',
                as_attachment=True,
                download_name='tts_output.wav'
            )
        finally:
            # Cleanup
            try:
                os.unlink(temp_filename)
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")

    except Exception as e:
        logger.error(f"Error in generate_audio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(Exception)
def handle_error(e):
    logger.error(f"Unhandled error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Disable werkzeug logging below WARNING level
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)

    # Enable threading for better performance
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(debug=True, threaded=True)