from flask import Flask, render_template, request, send_file, jsonify
import pyttsx3
import os
import tempfile

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

        # Initialize text-to-speech engine
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[voice_type].id)
        engine.setProperty('rate', speed)

        # Create temporary file for audio
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, 'output.wav')

        # Generate audio file
        engine.save_to_file(text, temp_file)
        engine.runAndWait()

        return send_file(
            temp_file,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='speech.wav'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)