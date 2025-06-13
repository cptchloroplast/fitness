import functions_framework
from flask import Request
import os
from garth.http import client
from sentry_sdk import init
from sentry_sdk.integrations.gcp import GcpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import bucket
from io import BytesIO
from json import dumps
import logging
import function

logger = logging.getLogger(__name__)

init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
    integrations=[
        GcpIntegration(),
        LoggingIntegration(),
    ],
    _experiments={
        "enable_logs": True
    }
)

token = os.getenv("GARMIN_TOKEN")
if not token:
    raise Exception("Unable to get token")
client.loads(token)

@functions_framework.http
@function.http(method="POST")
def garmin_upload(request: Request):
    file = request.files.get("file")
    if (not file):
        return "Missing file", 400
    result = client.upload(file) # type: ignore
    return result  

@functions_framework.http
@function.http(method="POST")
def garmin_download(request: Request):
    response = bucket.list(bucket.BUCKET)
    files = list(map(lambda x: x.get("Key"), response.get("Contents", []))) # type: ignore
    logger.info("Found %d files in bucket %s", len(files), bucket.BUCKET)
    existing = dict.fromkeys(files, True)
    activities = client.connectapi("/activitylist-service/activities/search/activities")
    ids = list(map(lambda x: x.get("activityId"), activities)) # type: ignore
    logger.info("Retrieved %d activities from Garmin", len(ids))
    processed = set()
    for id in ids:
        for (key, bytes) in {
            f"activity/{id}.json": lambda: str.encode(dumps(client.connectapi(f"/activity-service/activity/{id}"))),
            f"activity/{id}.fit": lambda: client.download(f"/download-service/files/activity/{id}"),
            f"activity/{id}.gpx": lambda: client.download(f"/download-service/export/gpx/activity/{id}"),
            f"activity/{id}.tcx": lambda: client.download(f"/download-service/export/tcx/activity/{id}"),
            f"activity/{id}.kml": lambda: client.download(f"/download-service/export/kml/activity/{id}"),
            f"activity/{id}.csv": lambda: client.download(f"/download-service/export/csv/activity/{id}"),
        }.items():
            if not existing.get(key):
                logger.info("Downloading file %s to bucket %s", key, bucket.BUCKET)
                bucket.upload(bucket.BUCKET, key, BytesIO(bytes()))
                processed.add(key)
    if len(processed):
        return f"Downloaded {len(processed)} files", 201
    else:
        return "No files downloaded", 200
