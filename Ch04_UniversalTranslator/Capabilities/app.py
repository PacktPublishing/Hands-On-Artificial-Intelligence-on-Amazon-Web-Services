from chalice import Chalice
from chalicelib import storage_service
from chalicelib import transcription_service
from chalicelib import translation_service
from chalicelib import speech_service


import cgi
from io import BytesIO
import json

#####
# chalice app configuration
#####
app = Chalice(app_name='Capabilities')
app.api.binary_types.append('multipart/form-data')
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
@app.route('/recordings', methods = ['POST'], content_types = ['multipart/form-data'], cors = True)
def upload_recording():
    """processes multipart upload and saves file to storage service"""
    uploaded_file = get_uploaded_file(app.current_request, 'file')

    file_name = uploaded_file["filename"]
    file_bytes = uploaded_file["bytes"]

    file_info = storage_service.upload_file(file_bytes, file_name)

    return file_info


@app.route('/recordings/{recording_id}/from-lang/{from_lang}/to-lang/{to_lang}/translated-text', methods = ['GET'], cors = True)
def transcribe_recording(recording_id, from_lang, to_lang):
    """transcribes the specified audio then translates the transcription text"""
    transcription_text = transcription_service.transcribe_audio(recording_id, from_lang)

    translation_text = translation_service.translate_text(transcription_text, target_language = to_lang)

    return {
        'text': transcription_text,
        'translation': translation_text
    }


@app.route('/synthesize_speech', methods = ['POST'], cors = True)
def synthesize_speech():
    """performs text-to-speech on the specified text / language"""
    request_data = json.loads(app.current_request.raw_body)

    translation_audio_url = speech_service.synthesize_speech(request_data['text'], request_data['language'])

    return {'audioUrl': translation_audio_url}


#####
# helper functions
#####
def get_uploaded_file(request, name):
    headers = request.headers
    raw_body = BytesIO(request.raw_body)

    form = cgi.FieldStorage(
        fp = raw_body,
        headers = headers,
        environ = {'REQUEST_METHOD': 'POST',
                   'CONTENT_TYPE': headers['content-type']})

    content_type = headers['content-type']

    _, parameters = cgi.parse_header(content_type)
    parameters['boundary'] = parameters['boundary'].encode('utf-8')
    # for python 3.7
    content_length = headers['content-length']
    parameters['CONTENT-LENGTH'] = content_length

    raw_body = BytesIO(app.current_request.raw_body)
    parts = cgi.parse_multipart(raw_body, parameters)

    return {"filename": form[name].filename, "bytes": parts[name][0]}
