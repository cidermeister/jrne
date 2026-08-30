import json
import pandas as pd
from datetime import datetime

def parse_timeline_data(json_data):
    """
    Parses the Google Maps Timeline JSON data and extracts activities,
    linking them to their origin and destination visits.
    """
    segments = json_data.get('semanticSegments', [])

    activities = []

    # Iterate through segments. We need to find 'activity' and the visits around it.
    for i in range(len(segments)):
        segment = segments[i]

        if 'activity' in segment:
            activity = segment['activity']

            # Default values
            start_place_id = None
            end_place_id = None
            start_lat = None
            start_lng = None
            end_lat = None
            end_lng = None

            # Find previous visit for origin
            if i > 0 and 'visit' in segments[i-1]:
                prev_visit = segments[i-1]['visit']
                top_candidate = prev_visit.get('topCandidate', {})
                start_place_id = top_candidate.get('placeId')
                if 'placeLocation' in top_candidate and 'latLng' in top_candidate['placeLocation']:
                    latlng_str = top_candidate['placeLocation']['latLng']
                    try:
                        # Format is typically "lat°, lng°"
                        lat_str, lng_str = latlng_str.replace('°', '').split(',')
                        start_lat = float(lat_str.strip())
                        start_lng = float(lng_str.strip())
                    except Exception:
                        pass

            # Find next visit for destination
            if i + 1 < len(segments) and 'visit' in segments[i+1]:
                next_visit = segments[i+1]['visit']
                top_candidate = next_visit.get('topCandidate', {})
                end_place_id = top_candidate.get('placeId')
                if 'placeLocation' in top_candidate and 'latLng' in top_candidate['placeLocation']:
                    latlng_str = top_candidate['placeLocation']['latLng']
                    try:
                        lat_str, lng_str = latlng_str.replace('°', '').split(',')
                        end_lat = float(lat_str.strip())
                        end_lng = float(lng_str.strip())
                    except Exception:
                        pass

            # Extract activity specifics
            activity_type = activity.get('topCandidate', {}).get('type', 'UNKNOWN')
            distance_meters = activity.get('distanceMeters', 0)

            # Fallback to activity start/end coordinates if visit places don't provide them
            if start_lat is None and 'start' in activity and 'latLng' in activity['start']:
                try:
                    lat_str, lng_str = activity['start']['latLng'].replace('°', '').split(',')
                    start_lat = float(lat_str.strip())
                    start_lng = float(lng_str.strip())
                except Exception:
                    pass

            if end_lat is None and 'end' in activity and 'latLng' in activity['end']:
                try:
                    lat_str, lng_str = activity['end']['latLng'].replace('°', '').split(',')
                    end_lat = float(lat_str.strip())
                    end_lng = float(lng_str.strip())
                except Exception:
                    pass

            # Try to parse start time from segment
            start_time = segment.get('startTime')
            end_time = segment.get('endTime')

            activities.append({
                'start_time': start_time,
                'end_time': end_time,
                'activity_type': activity_type,
                'distance_meters': distance_meters,
                'start_place_id': start_place_id,
                'end_place_id': end_place_id,
                'start_lat': start_lat,
                'start_lng': start_lng,
                'end_lat': end_lat,
                'end_lng': end_lng
            })

    df = pd.DataFrame(activities)

    if not df.empty:
        # Convert times to datetime objects
        df['start_time'] = pd.to_datetime(df['start_time'], utc=True)
        df['end_time'] = pd.to_datetime(df['end_time'], utc=True)
        # Add a distance in km column for easier filtering
        df['distance_km'] = df['distance_meters'] / 1000.0

    return df
