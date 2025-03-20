from flask import Flask, render_template, request, send_file, jsonify
from gtts import gTTS
from gtts.tts import gTTSError
import os
import tempfile
import uuid
import time
import logging
from requests.exceptions import RequestException

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_text():
    temp_file = None
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

        # Create a unique filename
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f'output_{uuid.uuid4()}.mp3')
        logger.debug(f'Created temporary file: {temp_file}')

        # Initialize text-to-speech with gTTS with retries
        max_retries = 3
        retry_delay = 1  # seconds
        logger.info('Starting text-to-speech conversion with retries')
        
        for attempt in range(max_retries):
            try:
                logger.info(f'Attempt {attempt + 1}/{max_retries} to convert text to speech')
                tts = gTTS(text=text, lang='en', slow=(speed < 100))
                logger.debug('gTTS object created successfully')
                tts.save(temp_file)
                logger.info('Audio file saved successfully')
                break
            except (gTTSError, RequestException) as e:
                logger.error(f'TTS attempt {attempt + 1} failed: {str(e)}, Error type: {type(e).__name__}')
                if attempt == max_retries - 1:
                    logger.error(f'All {max_retries} attempts failed. Last error: {str(e)}')
                    raise Exception(f'Failed to convert text after {max_retries} attempts: {str(e)}')
                logger.info(f'Waiting {retry_delay} seconds before retry')
                time.sleep(retry_delay)

        # Verify the file was created successfully
        if not os.path.exists(temp_file):
            logger.error('Audio file not found after conversion')
            raise Exception('Failed to create audio file')

        # Get file size to set Content-Length header
        file_size = os.path.getsize(temp_file)
        logger.debug(f'Audio file size: {file_size} bytes')

        def generate():
            try:
                logger.info('Starting audio file streaming')
                with open(temp_file, 'rb') as f:
                    data = f.read(8192)
                    while data:
                        yield data
                        data = f.read(8192)
                logger.info('Audio file streaming completed')
                # Clean up the file after sending
                if os.path.exists(temp_file):
                    logger.debug('Cleaning up temporary audio file')
                    os.remove(temp_file)
                    logger.info('Temporary audio file removed successfully')
            except Exception as e:
                logger.error(f'Error during file streaming: {str(e)}')
                raise

        response = app.response_class(
            generate(),
            mimetype='audio/mpeg'
        )
        response.headers['Content-Length'] = file_size
        response.headers['Content-Disposition'] = 'attachment; filename=speech.mp3'
        return response

    except ValueError as e:
        logger.error(f'Parameter validation error: {str(e)}, Error type: {type(e).__name__}')
        return jsonify({'error': f'Invalid parameter values: {str(e)}'}), 400
    except (gTTSError, RequestException) as e:
        logger.error(f'Network or TTS service error: {str(e)}, Error type: {type(e).__name__}')
        if temp_file and os.path.exists(temp_file):
            try:
                logger.debug('Attempting to clean up temporary file after error')
                os.remove(temp_file)
                logger.info('Successfully cleaned up temporary file after error')
            except Exception as cleanup_error:
                logger.error(f'Failed to remove temporary file: {str(cleanup_error)}, Error type: {type(cleanup_error).__name__}')
        return jsonify({'error': f'Network error occurred during text-to-speech conversion: {str(e)}. Please try again.'}), 503
    except Exception as e:
        logger.error(f'Unexpected error during text-to-speech conversion: {str(e)}, Error type: {type(e).__name__}')
        if temp_file and os.path.exists(temp_file):
            try:
                logger.debug('Attempting to clean up temporary file after error')
                os.remove(temp_file)
                logger.info('Successfully cleaned up temporary file after error')
            except Exception as cleanup_error:
                logger.error(f'Failed to remove temporary file: {str(cleanup_error)}, Error type: {type(cleanup_error).__name__}')
        return jsonify({'error': f'Failed to convert text to speech: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)