import boto3


class StorageService:
    def __init__(self, storage_location):
        self.client = boto3.client('s3')
        self.bucket_name = storage_location

    def get_storage_location(self):
        return self.bucket_name

    def list_files(self):
        response = self.client.list_objects_v2(Bucket = self.bucket_name)

        files = []
        for content in response['Contents']:
            files.append({
                'location': self.bucket_name,
                'file_name': content['Key'],
                'url': "http://" + self.bucket_name + ".s3.amazonaws.com/"
                       + content['Key']
            })
        return files
