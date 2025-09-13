import os
from flask import Request
from sentry_sdk import init
from sentry_sdk.integrations.gcp import GcpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
    integrations=[
        GcpIntegration(),
        LoggingIntegration(),
    ],
    enable_logs=True,
)

def http(method="GET"):
    def decorator(handler):
        def wrapper(request: Request):
            if request.method.upper() != method.upper():
                return "Not found", 404
            return handler(request)
        return wrapper
    return decorator
