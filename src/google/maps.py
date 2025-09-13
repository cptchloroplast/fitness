from typing import Tuple, List
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib import colormaps
from io import BytesIO
from pandas import DataFrame
import numpy as np
from datetime import datetime, timezone

def heatmap(center: Tuple[float, float], rows: List, padding = .2, size = 2500, width = 1):
    """Render heatmap as bytes"""

    # Initialize figure and array
    figsize = size / 100
    fig = Figure(figsize=(figsize, figsize), frameon=False)
    ax = fig.add_subplot()
    data = np.zeros((size, size))

    # Remove spines and ticks
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])

    # Get min and max coordinates to render
    lat_min = center[0] - padding
    lat_max = center[0] + padding
    lon_min = center[1] - padding
    lon_max = center[1] + padding

    # Create dataframe and trim to min and max coordinates
    df = DataFrame(rows, columns=["file", "lat", "lon"])
    trimmed = df[(df["lat"] > lat_min) & (df["lat"] < lat_max) & (df["lon"] > lon_min) & (df["lon"] < lon_max)].copy()

    # Convert geographic coordinates to integer cartesian coordinates
    trimmed["x"] = (size * (trimmed["lon"] - trimmed["lon"].min()) / (trimmed["lon"].max() - trimmed["lon"].min())).astype(int)
    trimmed["y"] = (size * (trimmed["lat"] - trimmed["lat"].min()) / (trimmed["lat"].max() - trimmed["lat"].min())).astype(int)

    #
    grouped = trimmed[["x", "y", "file"]].groupby(["x", "y"]).count().reset_index()
    for index, row in grouped.iterrows():
        x = int(row["x"])
        y = int(row["y"])
        data[y - width:y + width, x - width:x + width] += row["file"]
    max = len(trimmed["file"].unique())
    data[data > max] = max
    data = (data - data.min()) / (data.max() - data.min())
    cmap = colormaps["hot"]

    # Render image and orient north towards top
    ax.imshow(cmap(data), origin="lower")
    ax.set_title(f"Local Bicycle Heatmap\nBen Okkema <ben@okkema.org>\nUpdated {datetime.now(timezone.utc).isoformat()}", loc="left")
    output = BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    return output.getvalue()
