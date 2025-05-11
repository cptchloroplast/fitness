import functions_framework
import flask
import os
from garth.http import client
import sentry_sdk
from sentry_sdk.integrations.gcp import GcpIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
    integrations=[
        GcpIntegration(),
    ],
)

@functions_framework.http
def run(request: flask.Request):
    if request.method.upper() != "POST":
        return "Not found", 404
    if ("file" not in request.files):
        return "Missing file", 400
    file = request.files.get("file")
    token = os.getenv("GARMIN_TOKEN")
    if not token:
        return "Unable to get token", 500
    client.loads(token)
    result = client.upload(file)
    return result