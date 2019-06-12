import boto3


class StorageService:
    def __init__(self, storage_location):
        self.client = boto3.client('s3')
        self.bucket_name = storage_location

    def get_storage_location(self):
        return self.bucket_name

    def upload_file(self, file_bytes, file_name):
        self.client.put_object(Bucket = self.bucket_name,
                               Body = file_bytes,
                               Key = file_name,
                               ACL = 'public-read')

        return {'fileId': file_name,
                'fileUrl': "http://" + self.bucket_name + ".s3.amazonaws.com/" + file_name}

    def get_file(self, file_name):
        response = self.client.get_object(Bucket = self.bucket_name, Key = file_name)

        return response['Body'].read().decode('utf-8')

    def make_file_public(self, uri):
        parts = uri.split('/')
        key = parts[-1]
        bucket_name = parts[-2]

        self.client.put_object_acl(Bucket = bucket_name,
                                   Key = key,
                                   ACL = 'public-read')
