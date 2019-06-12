from chalice import Chalice
from chalicelib import storage_service
from chalicelib import recognition_service
from chalicelib import translation_service

import cgi
from io import BytesIO

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
recognition_service = recognition_service.RecognitionService(storage_service)
translation_service = translation_service.TranslationService()


#####
# RESTful endpoints
#####
@app.route('/images', methods = ['POST'], content_types = ['multipart/form-data'], cors = True)
def upload_image():
    """processes multipart upload and saves file to storage service"""
    uploaded_file = get_uploaded_file(app.current_request, 'file')

    file_name = uploaded_file["filename"]
    file_bytes = uploaded_file["bytes"]

    image_info = storage_service.upload_file(file_bytes, file_name)

    return image_info


@app.route('/images/{image_id}/from-lang/{from_lang}/to-lang/{to_lang}/translated-text', methods = ['GET'], cors = True)
def translate_image_text(image_id, from_lang, to_lang):
    """detects then translates text in the specified image"""
    MIN_CONFIDENCE = 80.0

    text_lines = recognition_service.detect_text(image_id)

    translated_lines = []
    for line in text_lines:
        # check confidence
        if float(line['confidence']) >= MIN_CONFIDENCE:
            translated_line = translation_service.translate_text(line['text'], from_lang, to_lang)
            translated_lines.append({
                'text': line['text'],
                'translation': translated_line,
                'boundingBox': line['boundingBox']
            })

    return translated_lines


#####
# helper functions
#####
def get_uploaded_file(request, name):
    """parses multipart request to extract uploaded file"""
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
