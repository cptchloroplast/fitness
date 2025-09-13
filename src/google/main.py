import functions_framework, gpxpy, json, logging
from flask import Request, Response
import bucket, functions, garmin, maps
from io import BytesIO

logger = logging.getLogger(__name__)

@functions_framework.http
@functions.http(method="POST")
def garmin_upload(request: Request):
    file = request.files.get("file")
    if (not file):
        return "Missing file", 400
    result = garmin.upload_activity(file)
    return result  

@functions_framework.http
@functions.http(method="POST")
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
            f"activity/{id}.json": lambda: str.encode(json.dumps(garmin.get_activity(id))),
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


@functions_framework.http
@functions.http()
def generate_heatmap(req: Request):
    center = (43.312222, -73.648333)
    files = list(filter(lambda x: x["Key"].endswith(".gpx"), bucket.list(bucket.BUCKET, "activity")))
    rows = []
    for file in files:
        key = file["Key"]
        bytes = bucket.download(bucket.BUCKET, key)
        gpx = gpxpy.parse(bytes)
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    lat, lon = point.latitude, point.longitude
                    rows.append([key, lat, lon])
    bytes = maps.heatmap(center, rows)
    return Response(bytes, mimetype="image/png")