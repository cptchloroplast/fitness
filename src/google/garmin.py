import os
from garth import client
from garth.exc import GarthHTTPError, GarthException
from typing import IO

def authenticate(handler):
    def wrapper(*args, **kwargs):
        if not client.oauth1_token or not client.oauth2_token:
            token = os.getenv("GARMIN_TOKEN")
            if not token:
                raise Exception("Unable to get token")
            client.loads(token)
        return handler(*args, **kwargs)
    return wrapper

@authenticate
def list_activity():
    return client.connectapi("/activitylist-service/activities/search/activities")

@authenticate
def get_activity(id: str):
    return client.connectapi(f"/activity-service/activity/{id}")

@authenticate
def download_activity(id: str, format: str | None = None):
    url = f"/download-service/export/{format}/activity/{id}" if format else f"/download-service/files/activity/{id}"
    return client.download(url)

@authenticate
def upload_activity(stream: IO[bytes]):
    try:
        return client.upload(stream)
    except GarthHTTPError as ex:
        if ex.error.response.status_code == 409: # duplicate activity
            return ex.error.response.json()
        raise ex