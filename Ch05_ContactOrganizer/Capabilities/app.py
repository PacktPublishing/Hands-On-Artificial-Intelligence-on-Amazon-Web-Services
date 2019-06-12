from chalice import Chalice
from chalicelib import storage_service
from chalicelib import recognition_service
from chalicelib import extraction_service
from chalicelib import contact_store

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
recognition_service = recognition_service.RecognitionService(storage_location)
extraction_service = extraction_service.ExtractionService()
store_location = 'Contacts'
contact_store = contact_store.ContactStore(store_location)


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


@app.route('/images/{image_id}/extracted-info', methods = ['GET'], cors = True)
def extract_image_info(image_id):
    """detects text in the specified image then extracts contact information from the text"""
    MIN_CONFIDENCE = 70.0

    text_lines = recognition_service.detect_text(image_id)

    contact_lines = []
    for line in text_lines:
        # check confidence
        if float(line['confidence']) >= MIN_CONFIDENCE:
            contact_lines.append(line['text'])

    contact_string = '   '.join(contact_lines)
    contact_info = extraction_service.extract_contact_info(contact_string)

    return contact_info


@app.route('/contacts', methods = ['POST'], cors = True)
def save_contact():
    """saves contact information to the contact store service"""
    request_data = json.loads(app.current_request.raw_body)

    contact = contact_store.save_contact(request_data)

    return contact


@app.route('/contacts', methods = ['GET'], cors = True)
def get_all_contacts():
    """gets all saved contacts in the contact store service"""
    contacts = contact_store.get_all_contacts()

    return contacts


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
