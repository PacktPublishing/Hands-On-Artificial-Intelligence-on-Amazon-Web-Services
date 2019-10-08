import boto3

class StorageService:
    def __init__(self):
        self.s3 = boto3.resource('s3')

    def get_all_files(self, storage_location):
        return self.s3.Bucket(storage_location).objects.all()

