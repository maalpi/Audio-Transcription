from flask import Flask, request, jsonify
import speech_recognition as sr
import moviepy.editor as mp
from pydub import AudioSegment
from flask_cors import CORS
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os

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

# Função para converter mp4 para wav, porque o speech_recognition so funciona com arquivos .WAV
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
#Defino o chunksize para porções de 60s para caber dentro dos limites da biblioteca
def transcribe_audio(audio_path, chunksize = 60000): 
    try:
        sound = AudioSegment.from_wav(audio_path)
        # Função para dividir o audios em partes de 60s
        def divide_chunks(sound, chunksize):
            # looping até o comprimento l
            for i in range(0, len(sound), chunksize):
                yield sound[i:i + chunksize]
        chunks = list(divide_chunks(sound, chunksize))
        print(f"{len(chunks)} chunks of {chunksize/1000}s each")

        recognizer = sr.Recognizer()
        string_index = {}

        for index, chunk in enumerate(chunks):
            temp = f'temp_{index}.wav'
            chunk.export(temp, format='wav')
            with sr.AudioFile(temp) as source:
                audio = recognizer.record(source)
            s = recognizer.recognize_google(audio, language="pt-BR")
            string_index[index] = s
            os.remove(temp)  # Remove o arquivo temporário após o uso

        return ' '.join([string_index[i] for i in range(len(string_index))])

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
