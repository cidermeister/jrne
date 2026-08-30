import os
import json
import location_manager

def test_location_manager():
    # Cleanup before test
    if os.path.exists(location_manager.LOCATION_FILE):
        os.remove(location_manager.LOCATION_FILE)

    assert location_manager.load_locations() == {}

    location_manager.save_location('PLACE_1', 'Home')
    location_manager.save_location('PLACE_2', 'Office')

    locations = location_manager.load_locations()
    assert locations['PLACE_1'] == 'Home'
    assert locations['PLACE_2'] == 'Office'

    assert location_manager.get_location_name('PLACE_1') == 'Home'
    assert location_manager.get_location_name('PLACE_3') == 'Unknown Location'
    assert location_manager.get_location_name(None) == 'Unknown Location'

if __name__ == '__main__':
    test_location_manager()
    print("Location Manager tests passed")
