import json
import pandas as pd
from data_parser import parse_timeline_data

def test_parse():
    sample_json = {
      "semanticSegments": [
        {
          "startTime": "2025-09-16T12:36:48.000+02:00",
          "endTime": "2025-09-16T13:22:54.000+02:00",
          "visit": {
            "topCandidate": {
              "placeId": "START_PLACE",
              "placeLocation": {
                "latLng": "47.1617103°, 8.298679°"
              }
            }
          }
        },
        {
          "startTime": "2025-09-16T14:04:40.000+02:00",
          "endTime": "2025-09-16T14:08:41.000+02:00",
          "activity": {
            "distanceMeters": 717.95,
            "topCandidate": {
              "type": "IN_PASSENGER_VEHICLE"
            },
            "start": { "latLng": "47.161868°, 8.2982824°" },
            "end": { "latLng": "47.1650112°, 8.2905861°" }
          }
        },
        {
          "startTime": "2025-09-16T14:08:41.000+02:00",
          "endTime": "2025-09-16T14:29:05.000+02:00",
          "visit": {
            "topCandidate": {
              "placeId": "END_PLACE",
              "placeLocation": {
                "latLng": "47.1658333°, 8.2916667°"
              }
            }
          }
        }
      ]
    }
    df = parse_timeline_data(sample_json)
    print(df['distance_km'])
    assert len(df) == 1
    assert df.iloc[0]['start_place_id'] == "START_PLACE"
    assert df.iloc[0]['end_place_id'] == "END_PLACE"
    assert df.iloc[0]['activity_type'] == "IN_PASSENGER_VEHICLE"
    assert abs(df.iloc[0]['distance_km'] - 0.71795) < 1e-5

if __name__ == '__main__':
    test_parse()
    print("Tests passed")
