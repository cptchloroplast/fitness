import boto3
from botocore.config import Config
import os
from typing import IO

BUCKET = "fitness"

config = Config(client_context_params={
  "request_checksum_calculation": "WHEN_REQUIRED",
  "response_checksum_validation": "WHEN_REQUIRED",
})

s3 = boto3.client(
  service_name="s3",
  endpoint_url = os.getenv("BUCKET_URL"),
  config=config
)

def list(bucket: str):
  return s3.list_objects(Bucket=bucket)

def upload(bucket: str, path: str, content: IO[bytes]):
  s3.upload_fileobj(content, bucket, path)