import difflib
import os

import speech_recognition as spr
from flask import Flask  # import flask
from flask_cors import CORS

from flask import request
from pydub import AudioSegment
from pydub.silence import split_on_silence

app = Flask(__name__)  # create an app instance
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/")
def hello():
    return "Running!"


@app.route("/stories")
def get_story():
    with open("story.txt", encoding="utf-8") as file:
        story = ''.join(file)
    return {
        'story': story
    }


@app.route("/videos", methods=["POST"])
def post_video():
    file_name = 'video'
    webm = f'{file_name}.webm'
    wav = f'{file_name}.wav'
    dir_path = os.path.dirname(os.path.realpath(__file__))

    if os.path.isfile(webm):
        os.remove(webm)
    if os.path.isfile(wav):
        os.remove(wav)

    with open(webm, "wb") as out_file:
        out_file.write(request.data)

    os.chdir(dir_path)

    webm_cmd = f'ffmpeg -i {webm} {wav}'
    os.system(webm_cmd)

    recognizer = spr.Recognizer()
    audio = AudioSegment.from_wav(f'{dir_path}/{wav}')

    # Split into chunks
    audio_chunks = split_on_silence(audio, min_silence_len=500, silence_thresh=audio.dBFS - 14, keep_silence=500)
    chunks_folder = f'{dir_path}/chunks'
    if not os.path.exists(chunks_folder):
        os.mkdir(chunks_folder)

    text = ''

    for i, chunk in enumerate(audio_chunks, start=1):
        chunk_filename = f'{chunks_folder}/chunk_{i}.wav'
        chunk.export(chunk_filename, format="wav")
        # Use speech recognition and recognize the chunk
        with spr.AudioFile(chunk_filename) as source:
            sentence_audio = recognizer.record(source)
            try:
                text += recognizer.recognize_google(sentence_audio) + '. '
            except spr.UnknownValueError as e:
                # print('Unknown value error')
                pass
    expected = get_story().get('story')
    return {
        'expected': get_story().get('story'),
        'received': text,
        'accuracy': round(difflib.SequenceMatcher(None, expected.lower(), text.lower()).ratio() * 100)
    }


if __name__ == "__main__":  # on running python app.py
    app.run()  # run the flask app
