from flask import Request

def http(method="GET"):
    def decorator(handler):
        def wrapper(request: Request):
            if request.method.upper() != method.upper():
                return "Not found", 404
            return handler(request)
        return wrapper
    return decorator