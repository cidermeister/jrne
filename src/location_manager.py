import json
import os

LOCATION_FILE = 'saved_locations.json'

def load_locations():
    """
    Loads saved location mappings from the JSON file.
    Returns a dictionary mapping placeId to a custom name.
    """
    if not os.path.exists(LOCATION_FILE):
        return {}

    try:
        with open(LOCATION_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_location(place_id, custom_name):
    """
    Saves a new location mapping to the JSON file.
    """
    locations = load_locations()
    locations[place_id] = custom_name

    with open(LOCATION_FILE, 'w') as f:
        json.dump(locations, f, indent=4)

    return locations

def get_location_name(place_id, default="Unknown Location"):
    """
    Retrieves the custom name for a placeId, or returns a default if not found.
    """
    if not place_id:
        return default
    locations = load_locations()
    return locations.get(place_id, default)
