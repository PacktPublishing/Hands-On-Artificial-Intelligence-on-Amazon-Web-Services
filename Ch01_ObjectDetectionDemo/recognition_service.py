import boto3

class RecognitionService:
    def __init__(self):
        self.client = boto3.client('rekognition')

    def detect_objects(self, storage_location, image_file):
        response = self.client.detect_labels(
            Image = {
                'S3Object': {
                    'Bucket': storage_location,
                    'Name': image_file
                }
            }
        )

        return response['Labels']

