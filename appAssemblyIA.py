from flask import Flask, request, jsonify
import assemblyai as aai
from flask_cors import CORS
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os

aai.settings.api_key = "apikey"

app = Flask(__name__)
CORS(app)  # Habilita CORS para todos os domínios

# Função para extrair áudio de um vídeo do YouTube
def extract_audio_from_youtube(url):
    try:
        yt = YouTube(url, on_progress_callback = on_progress)
        print(yt.title)
        video = yt.streams.get_audio_only()

        if not video:
            raise ValueError("No audio stream available")
        audio_path = video.download(filename="audio.mp3")
        
        print(f"Audio downloaded to: {audio_path}")
        return audio_path
    except Exception as e:
        print(f"ERROR ao extrair audio: {str(e)}")
        raise

# Função para converter mp4 para wav
def upload_to_assemblyai(audio_path):
    
    config = aai.TranscriptionConfig(language_code="pt")
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_path)

    return(transcript.text)

# Rota para transcrever o vídeo
@app.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.json
    print(f"Received request with data: {data}")
    if 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400

    url = data['url']

    try:
        audio_path = extract_audio_from_youtube(url)
        transcrever = upload_to_assemblyai(audio_path)
        print(transcrever       )
        os.remove(audio_path)
        return jsonify({'transcription': transcrever})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Inicializando
if __name__ == '__main__':
    app.run(debug=True)
