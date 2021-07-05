from .ws_single import load_csv
from .ws_map import load_map


recipe_workshop_map = {
    "descr": "QMAP as zipped comma-separated values",
    "loader": load_map,
    "suffix": ".zip",
    "modalities": ["force-distance"],
    "maker": "AFM workshop",
}

recipe_workshop_single = {
    "descr": "comma-separated values",
    "loader": load_csv,
    "suffix": ".csv",
    "modalities": ["force-distance"],
    "maker": "AFM workshop",
}
