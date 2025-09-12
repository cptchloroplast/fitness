import functions_framework
from flask import Request, Response
import os
from sentry_sdk import init
from sentry_sdk.integrations.gcp import GcpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import bucket
from io import BytesIO
from json import dumps
import logging
import function
import gpxpy
import maps
import fit
import garmin

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

@functions_framework.http
@function.http(method="POST")
def garmin_upload(request: Request):
    file = request.files.get("file")
    if (not file):
        return "Missing file", 400
    modified = fit.process(file) # type: ignore
    result = garmin.upload_activity(file)
    return result  

@functions_framework.http
@function.http(method="POST")
def garmin_download(request: Request):
    response = bucket.list(bucket.BUCKET)
    files = list(map(lambda x: x.get("Key"), response))
    logger.info("Found %d files in bucket %s", len(files), bucket.BUCKET)
    existing = dict.fromkeys(files, True)
    activities = garmin.list_activity()
    ids = list(map(lambda x: x.get("activityId"), activities)) # type: ignore
    logger.info("Retrieved %d activities from Garmin", len(ids))
    processed = set()
    for id in ids:
        for (key, bytes) in {
            f"activity/{id}.json": lambda: str.encode(dumps(garmin.get_activity(id))),
            f"activity/{id}.fit": lambda: garmin.download_activity(id),
            f"activity/{id}.gpx": lambda: garmin.download_activity(id, "gpx"),
            f"activity/{id}.tcx": lambda: garmin.download_activity(id, "tcx"),
            f"activity/{id}.kml": lambda: garmin.download_activity(id, "kml"),
            f"activity/{id}.csv": lambda: garmin.download_activity(id, "csv"),
        }.items():
            if not existing.get(key):
                logger.info("Downloading file %s to bucket %s", key, bucket.BUCKET)
                bucket.upload(bucket.BUCKET, key, BytesIO(bytes()))
                processed.add(key)
    if len(processed):
        return f"Downloaded {len(processed)} files", 201
    else:
        return "No files downloaded", 200
