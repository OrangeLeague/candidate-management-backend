# utils/backblaze.py
import boto3
from django.conf import settings

class BackblazeB2:
    def __init__(self):
        print(settings.BACKBLAZE_ENDPOINT_URL,ettings.BACKBLAZE_ACCESS_KEY,settings.BACKBLAZE_SECRET_KEY,'sdfhsdfsdfsdf')
        self.s3 = boto3.client(
            's3',
            endpoint_url=settings.BACKBLAZE_ENDPOINT_URL,
            aws_access_key_id=settings.BACKBLAZE_ACCESS_KEY,
            aws_secret_access_key=settings.BACKBLAZE_SECRET_KEY,
        )
        self.bucket_name = settings.BACKBLAZE_BUCKET_NAME

    def upload_file(self, file_path, object_name):
        """Upload a file to the bucket."""
        try:
            self.s3.upload_file(file_path, self.bucket_name, object_name)
            return f"{settings.BACKBLAZE_ENDPOINT_URL}/{self.bucket_name}/{object_name}"
        except Exception as e:
            raise Exception(f"Failed to upload file: {e}")

    def get_file_url(self, object_name):
        """Generate a public URL for a file."""
        return f"{settings.BACKBLAZE_ENDPOINT_URL}/{self.bucket_name}/{object_name}"
