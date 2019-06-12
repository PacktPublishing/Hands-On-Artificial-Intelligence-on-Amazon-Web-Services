from chalice import Chalice
from chalicelib import intelligent_assistant_service

import json

#####
# chalice app configuration
#####
app = Chalice(app_name='Capabilities')
app.debug = True

#####
# services initialization
#####
assistant_name = 'ContactAssistant'
assistant_service = intelligent_assistant_service.IntelligentAssistantService(assistant_name)


#####
# RESTful endpoints
#####
@app.route('/contact-assistant/user-id/{user_id}/send-text', methods = ['POST'], cors = True)
def send_user_text(user_id):
    request_data = json.loads(app.current_request.raw_body)

    message = assistant_service.send_user_text(user_id, request_data['text'])

    return message
