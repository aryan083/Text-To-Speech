from flask import Flask, render_template, request, send_file, jsonify
from gtts import gTTS
from gtts.tts import gTTSError
import os
import tempfile
import uuid
import time
from requests.exceptions import RequestException

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_text():
    temp_file = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        text = data.get('text', '')
        voice_type = int(data.get('voice', 0))  # 0 for male, 1 for female
        speed = int(data.get('speed', 100))

        if not text.strip():
            return jsonify({'error': 'Please enter some text'}), 400

        # Create a unique filename
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f'output_{uuid.uuid4()}.mp3')

        # Initialize text-to-speech with gTTS with retries
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                tts = gTTS(text=text, lang='en', slow=(speed < 100))
                tts.save(temp_file)
                break
            except (gTTSError, RequestException) as e:
                app.logger.error(f'TTS attempt {attempt + 1} failed: {str(e)}')
                if attempt == max_retries - 1:
                    raise Exception(f'Failed to convert text after {max_retries} attempts: {str(e)}')
                time.sleep(retry_delay)

        # Verify the file was created successfully
        if not os.path.exists(temp_file):
            raise Exception('Failed to create audio file')

        # Get file size to set Content-Length header
        file_size = os.path.getsize(temp_file)

        def generate():
            with open(temp_file, 'rb') as f:
                data = f.read(8192)
                while data:
                    yield data
                    data = f.read(8192)
            # Clean up the file after sending
            if os.path.exists(temp_file):
                os.remove(temp_file)

        response = app.response_class(
            generate(),
            mimetype='audio/mpeg'
        )
        response.headers['Content-Length'] = file_size
        response.headers['Content-Disposition'] = 'attachment; filename=speech.mp3'
        return response

    except ValueError as e:
        app.logger.error(f'Parameter validation error: {str(e)}')
        return jsonify({'error': 'Invalid parameter values'}), 400
    except (gTTSError, RequestException) as e:
        app.logger.error(f'Network or TTS service error: {str(e)}')
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as cleanup_error:
                app.logger.error(f'Failed to remove temporary file: {str(cleanup_error)}')
        return jsonify({'error': 'Network error occurred during text-to-speech conversion. Please try again.'}), 503
    except Exception as e:
        app.logger.error(f'Text-to-speech conversion error: {str(e)}')
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as cleanup_error:
                app.logger.error(f'Failed to remove temporary file: {str(cleanup_error)}')
        return jsonify({'error': 'Failed to convert text to speech'}), 500

if __name__ == '__main__':
    app.run(debug=True)