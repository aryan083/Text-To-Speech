from flask import Flask, render_template, request, send_file, jsonify
from gtts import gTTS
import os
import tempfile
import uuid

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice_type = int(data.get('voice', 0))  # 0 for male, 1 for female
        speed = int(data.get('speed', 100))

        if not text.strip():
            return jsonify({'error': 'Please enter some text'}), 400

        # Create a unique filename
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f'output_{uuid.uuid4()}.mp3')

        # Initialize text-to-speech with gTTS
        tts = gTTS(text=text, lang='en', slow=(speed < 100))
        
        # Save the audio file
        tts.save(temp_file)

        return send_file(
            temp_file,
            mimetype='audio/mp3',
            as_attachment=True,
            download_name='speech.wav'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)