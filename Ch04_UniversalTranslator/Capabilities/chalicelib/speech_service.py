import boto3
import time


class SpeechService:
    def __init__(self, storage_service):
        self.client = boto3.client('polly')
        self.bucket_name = storage_service.get_storage_location()
        self.storage_service = storage_service

    def synthesize_speech(self, text, target_language):
        POLL_DELAY = 5

        voice_map = {
            'en': 'Ivy',
            'de': 'Marlene',
            'fr': 'Celine',
            'it': 'Carla',
            'es': 'Conchita'
        }

        response = self.client.start_speech_synthesis_task(
            Text = text,
            VoiceId = voice_map[target_language],
            OutputFormat = 'mp3',
            OutputS3BucketName = self.bucket_name
        )

        synthesis_task = {
            'taskId': response['SynthesisTask']['TaskId'],
            'taskStatus': 'inProgress'
        }

        while synthesis_task['taskStatus'] == 'inProgress'\
                or synthesis_task['taskStatus'] == 'scheduled':
            time.sleep(POLL_DELAY)

            response = self.client.get_speech_synthesis_task(
                TaskId = synthesis_task['taskId']
            )

            synthesis_task['taskStatus'] = response['SynthesisTask']['TaskStatus']

            if synthesis_task['taskStatus'] == 'completed':
                synthesis_task['speechUri'] = response['SynthesisTask']['OutputUri']
                self.storage_service.make_file_public(synthesis_task['speechUri'])
                return synthesis_task['speechUri']

        return ''
