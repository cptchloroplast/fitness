import boto3
from botocore.config import Config
from types_boto3_s3.type_defs import ObjectTypeDef
import os
from typing import IO, List

BUCKET = "fitness"

config = Config(client_context_params={
  "request_checksum_calculation": "WHEN_REQUIRED",
  "response_checksum_validation": "WHEN_REQUIRED",
})

s3 = boto3.client(
  service_name="s3", # type: ignore
  endpoint_url = os.getenv("BUCKET_URL"),
  config=config
)

def list(bucket: str, prefix=""):
  objects: List[ObjectTypeDef] = []
  result = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
  objects += result["Contents"] # type: ignore
  token = result.get("NextContinuationToken")
  while token:
    result = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, ContinuationToken=token)
    objects += result["Contents"] # type: ignore
    token = result.get("NextContinuationToken")
  return objects

def upload(bucket: str, path: str, content: IO[bytes]):
  s3.upload_fileobj(content, bucket, path)

def download(bucket: str, key: str):
  data = s3.get_object(Bucket=bucket, Key=key)
  return data["Body"].read()
