import functions_framework
import flask
import os
from garth.http import client

@functions_framework.http
def run(request: flask.Request):
    token = os.getenv("GARMIN_TOKEN")
    if not token:
        return "Unable to get token", 500
    client.loads(token)
    return client.profile