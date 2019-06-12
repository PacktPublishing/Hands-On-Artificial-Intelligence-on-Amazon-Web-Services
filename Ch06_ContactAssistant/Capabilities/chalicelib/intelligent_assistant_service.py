import boto3


class IntelligentAssistantService:
    def __init__(self, assistant_name):
        self.client = boto3.client('lex-runtime')
        self.assistant_name = assistant_name

    def send_user_text(self, user_id, input_text):
        response = self.client.post_text(
            botName = self.assistant_name,
            botAlias = 'Production',
            userId = user_id,
            inputText = input_text
        )

        return response['message']
