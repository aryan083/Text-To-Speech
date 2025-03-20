from flask import Flask, render_template, request, send_file, jsonify, Response
from gtts import gTTS
from gtts.tts import gTTSError
import os
import io
import time
import logging
from requests.exceptions import RequestException
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
        
        logger.debug(f'Received parameters - Text length: {len(text)}, Voice type: {voice_type}, Speed: {speed}')

        if not text.strip():
            logger.warning('Empty text received')
            return jsonify({'error': 'Please enter some text'}), 400

        # Initialize text-to-speech with gTTS with retries
        max_retries = 3
        retry_delay = 1  # seconds
        logger.info('Starting text-to-speech conversion with retries')
        
        audio_data = None
        for attempt in range(max_retries):
            try:
                logger.info(f'Attempt {attempt + 1}/{max_retries} to convert text to speech')
                tts = gTTS(text=text, lang='en', slow=(speed < 100))
                logger.debug('gTTS object created successfully')
                
                # Use BytesIO instead of temporary file
                audio_io = io.BytesIO()
                tts.write_to_fp(audio_io)
                audio_data = audio_io.getvalue()
                logger.info('Audio data generated successfully in memory')
                break
            except (gTTSError, RequestException) as e:
                logger.error(f'TTS attempt {attempt + 1} failed: {str(e)}, Error type: {type(e).__name__}')
                if attempt == max_retries - 1:
                    logger.error(f'All {max_retries} attempts failed. Last error: {str(e)}')
                    raise Exception(f'Failed to convert text after {max_retries} attempts: {str(e)}')
                logger.info(f'Waiting {retry_delay} seconds before retry')
                time.sleep(retry_delay)

        if not audio_data:
            logger.error('Audio data not generated')
            raise Exception('Failed to generate audio data')

        # Create response with in-memory audio data
        response = Response(
            audio_data,
            mimetype='audio/mpeg'
        )
        response.headers['Content-Length'] = len(audio_data)
        response.headers['Content-Disposition'] = 'attachment; filename=speech.mp3'
        return response

    except ValueError as e:
        logger.error(f'Parameter validation error: {str(e)}, Error type: {type(e).__name__}')
        return jsonify({'error': f'Invalid parameter values: {str(e)}'}), 400
    except (gTTSError, RequestException) as e:
        logger.error(f'Network or TTS service error: {str(e)}, Error type: {type(e).__name__}')
        if 'temp_file' in locals() and temp_file and os.path.exists(temp_file):
            try:
                logger.debug('Attempting to clean up temporary file after error')
                os.remove(temp_file)
                logger.info('Successfully cleaned up temporary file after error')
            except Exception as cleanup_error:
                logger.error(f'Failed to remove temporary file: {str(cleanup_error)}, Error type: {type(cleanup_error).__name__}')
        return jsonify({'error': f'Network error occurred during text-to-speech conversion: {str(e)}. Please try again.'}), 503
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