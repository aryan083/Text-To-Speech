from flask import Flask, render_template, request, send_file, jsonify, Response
import pyttsx3
import os
import io
import time
import logging
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

# Configure for running behind a proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_and_install_espeak():
    try:
        # Check if espeak is installed
        subprocess.run(["espeak", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("eSpeak is already installed.")
    except FileNotFoundError:
        print("eSpeak not found! Installing...")
        try:
            subprocess.run(["pip", "install", "espeak-ng"], check=True)
            print("eSpeak installed successfully.")
        except subprocess.CalledProcessError:
            print("Failed to install eSpeak. Please install it manually.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_text():
    try:
        logger.info('Starting text-to-speech conversion request')
        data = request.get_json()
        if not data:
            logger.warning('Invalid JSON data received')
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        text = data.get('text', '')
        voice_type = int(data.get('voice', 0))  # 0 for male, 1 for female
        speed = int(data.get('speed', 100))
        
        # Validate speed range
        if not (50 <= speed <= 150):
            raise ValueError('Speed must be between 50 and 150')
        
        logger.debug(f'Received parameters - Text length: {len(text)}, Voice type: {voice_type}, Speed: {speed}')

        if not text.strip():
            logger.warning('Empty text received')
            return jsonify({'error': 'Please enter some text'}), 400

        # Run the check
        check_and_install_espeak()
        # Initialize pyttsx3 engine
        engine = pyttsx3.init()
        
        # Get and set voice type
        voices = engine.getProperty('voices')
        # Map voice_type (0 for male, 1 for female) to the correct voice index
        # On Windows, typically index 0 is David (Male) and index 1 is Zira (Female)
        voice_index = 0 if voice_type == 0 else 1
        if voice_index < len(voices):
            engine.setProperty('voice', voices[voice_index].id)
        
        # Set speech rate (speed)
        # Convert speed value to pyttsx3 rate (words per minute)
        # Map 50-150 range to 100-200 wpm for better speed control
        rate = int(100 + (speed - 50))
        engine.setProperty('rate', rate)
        
        # Use BytesIO to store audio data
        audio_io = io.BytesIO()
        
        # Save the synthesized speech to the BytesIO buffer
        engine.save_to_file(text, 'temp.wav')
        engine.runAndWait()
        
        # Read the temporary file into memory and delete it
        with open('temp.wav', 'rb') as f:
            audio_data = f.read()
        os.remove('temp.wav')
        
        logger.info('Audio data generated successfully')


        if not audio_data:
            logger.error('Audio data not generated')
            raise Exception('Failed to generate audio data')

        # Create response with in-memory audio data
        response = Response(
            audio_data,
            mimetype='audio/wav'
        )
        response.headers['Content-Length'] = len(audio_data)
        response.headers['Content-Disposition'] = 'attachment; filename=speech.wav'
        return response

    except ValueError as e:
        logger.error(f'Parameter validation error: {str(e)}, Error type: {type(e).__name__}')
        return jsonify({'error': f'Invalid parameter values: {str(e)}'}), 400
    except Exception as e:
        logger.error(f'Unexpected error during text-to-speech conversion: {str(e)}, Error type: {type(e).__name__}')
        if os.path.exists('temp.wav'):
            try:
                os.remove('temp.wav')
                logger.info('Successfully cleaned up temporary file after error')
            except Exception as cleanup_error:
                logger.error(f'Failed to remove temporary file: {str(cleanup_error)}')
        return jsonify({'error': f'Failed to convert text to speech: {str(e)}'}), 500
    except Exception as e:
        logger.error(f'Unexpected error during text-to-speech conversion: {str(e)}, Error type: {type(e).__name__}')
        if 'temp_file' in locals() and temp_file and os.path.exists(temp_file):
            try:
                logger.debug('Attempting to clean up temporary file after error')
                os.remove(temp_file)
                logger.info('Successfully cleaned up temporary file after error')
            except Exception as cleanup_error:
                logger.error(f'Failed to remove temporary file: {str(cleanup_error)}, Error type: {type(cleanup_error).__name__}')
        return jsonify({'error': f'Failed to convert text to speech: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)