from chalice import Chalice
from chalicelib import storage_service
from chalicelib import transcription_service
from chalicelib import translation_service
from chalicelib import speech_service


import base64
import json

#####
# chalice app configuration
#####
app = Chalice(app_name='Capabilities')
app.debug = True

#####
# services initialization
#####
storage_location = 'contents.aws.ai'
storage_service = storage_service.StorageService(storage_location)
transcription_service = transcription_service.TranscriptionService(storage_service)
translation_service = translation_service.TranslationService()
speech_service = speech_service.SpeechService(storage_service)


#####
# RESTful endpoints
#####
@app.route('/recordings', methods = ['POST'], cors = True)
def upload_recording():
    """processes file upload and saves file to storage service"""
    request_data = json.loads(app.current_request.raw_body)
    file_name = request_data['filename']
    file_bytes = base64.b64decode(request_data['filebytes'])

    file_info = storage_service.upload_file(file_bytes, file_name)

    return file_info


@app.route('/recordings/{recording_id}/translate-text', methods = ['POST'], cors = True)
def translate_recording(recording_id):
    """transcribes the specified audio then translates the transcription text"""
    request_data = json.loads(app.current_request.raw_body)
    from_lang = request_data['fromLang']
    to_lang = request_data['toLang']

    transcription_text = transcription_service.transcribe_audio(recording_id, from_lang)

    translation_text = translation_service.translate_text(transcription_text,
                                                          target_language = to_lang)

    return {
        'text': transcription_text,
        'translation': translation_text
    }


@app.route('/synthesize_speech', methods = ['POST'], cors = True)
def synthesize_speech():
    """performs text-to-speech on the specified text / language"""
    request_data = json.loads(app.current_request.raw_body)
    text = request_data['text']
    language = request_data['language']

    translation_audio_url = speech_service.synthesize_speech(text, language)

    return {
        'audioUrl': translation_audio_url
    }
