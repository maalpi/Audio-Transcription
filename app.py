from flask import Flask, request, jsonify
import speech_recognition as sr
import moviepy.editor as mp
from pydub import AudioSegment
# from pytube import YouTube
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os

app = Flask(__name__)

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
def convert_audio_to_wav(audio_path):
    try:
        audio = AudioSegment.from_file(audio_path)
        wav_path = audio_path.replace('.mp3', '.wav')
        audio.export(wav_path, format="wav")
        print(f"Audio converted to: {wav_path}")
        return wav_path
    except Exception as e:
        print(f"ERROR ao converter audio: {str(e)}")
        raise

# Função para transcrever áudio
def transcribe_audio(audio_path):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='pt-BR')
        print(f"Transcription result: {text}")
        return text
    except Exception as e:
        print(f"Error transcribing audio: {str(e)}")
        raise

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
        wav_path = convert_audio_to_wav(audio_path)
        transcription = transcribe_audio(wav_path)
        os.remove(audio_path)
        os.remove(wav_path)
        return jsonify({'transcription': transcription})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Inicializando
if __name__ == '__main__':
    app.run(debug=True)
