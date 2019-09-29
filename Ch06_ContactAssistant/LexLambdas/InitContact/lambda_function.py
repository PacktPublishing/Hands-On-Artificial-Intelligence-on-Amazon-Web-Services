def lex_lambda_handler(event, context):
    intent_name = event['currentIntent']['name']
    parameters = event['currentIntent']['slots']
    attributes = event['sessionAttributes'] if event['sessionAttributes'] is not None else {}

    response = init_contact(intent_name, parameters, attributes)

    return response


def init_contact(intent_name, parameters, attributes):
    first_name = parameters.get('FirstName')
    last_name = parameters.get('LastName')

    prev_first_name = attributes.get('FirstName')
    prev_last_name = attributes.get('LastName')

    if first_name is None and prev_first_name is not None:
        parameters['FirstName'] = prev_first_name

    if last_name is None and prev_last_name is not None:
        parameters['LastName'] = prev_last_name

    if parameters['FirstName'] is not None and parameters['LastName'] is not None:
        response = intent_delegation(intent_name, parameters, attributes)
    elif parameters['FirstName'] is None:
        response = intent_elicitation(intent_name, parameters, attributes, 'FirstName')
    elif parameters['LastName'] is None:
        response = intent_elicitation(intent_name, parameters, attributes, 'LastName')

    return response


#####
# lex response helper functions
#####
def intent_success(intent_name, parameters, attributes):
    return {
        'sessionAttributes': attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': 'Fulfilled'
        }
    }


def intent_failure(intent_name, parameters, attributes, message):
    return {
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': 'Failed',
            'message': {
                'contentType': 'PlainText',
                'content': message
            }
        }
    }


def intent_delegation(intent_name, parameters, attributes):
    return {
        'sessionAttributes': attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': parameters,

        }
    }


def intent_elicitation(intent_name, parameters, attributes, parameter_name):
    return {
        'sessionAttributes': attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': parameters,
            'slotToElicit': parameter_name
        }
    }
