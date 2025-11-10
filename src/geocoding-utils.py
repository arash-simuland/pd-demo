"""
geocoding-utils.py - Geocoding utilities for dynamic node creation

Converts city/state names to latitude/longitude coordinates.
Uses geopy with fallback to hardcoded US city database.
"""

from typing import Optional, Tuple


# Fallback database of US cities (lat, lon)
US_CITIES = {
    ("atlanta", "ga"): (33.7490, -84.3880),
    ("atlanta", "georgia"): (33.7490, -84.3880),
    ("dallas", "tx"): (32.7767, -96.7970),
    ("dallas", "texas"): (32.7767, -96.7970),
    ("miami", "fl"): (25.7617, -80.1918),
    ("miami", "florida"): (25.7617, -80.1918),
    ("boston", "ma"): (42.3601, -71.0589),
    ("boston", "massachusetts"): (42.3601, -71.0589),
    ("seattle", "wa"): (47.6062, -122.3321),
    ("seattle", "washington"): (47.6062, -122.3321),
    ("denver", "co"): (39.7392, -104.9903),
    ("denver", "colorado"): (39.7392, -104.9903),
    ("phoenix", "az"): (33.4484, -112.0740),
    ("phoenix", "arizona"): (33.4484, -112.0740),
    ("houston", "tx"): (29.7604, -95.3698),
    ("houston", "texas"): (29.7604, -95.3698),
    ("philadelphia", "pa"): (39.9526, -75.1652),
    ("philadelphia", "pennsylvania"): (39.9526, -75.1652),
    ("san antonio", "tx"): (29.4241, -98.4936),
    ("san antonio", "texas"): (29.4241, -98.4936),
    ("san diego", "ca"): (32.7157, -117.1611),
    ("san diego", "california"): (32.7157, -117.1611),
    ("san jose", "ca"): (37.3382, -121.8863),
    ("san jose", "california"): (37.3382, -121.8863),
    ("austin", "tx"): (30.2672, -97.7431),
    ("austin", "texas"): (30.2672, -97.7431),
    ("jacksonville", "fl"): (30.3322, -81.6557),
    ("jacksonville", "florida"): (30.3322, -81.6557),
    ("columbus", "oh"): (39.9612, -82.9988),
    ("columbus", "ohio"): (39.9612, -82.9988),
    ("charlotte", "nc"): (35.2271, -80.8431),
    ("charlotte", "north carolina"): (35.2271, -80.8431),
    ("indianapolis", "in"): (39.7684, -86.1581),
    ("indianapolis", "indiana"): (39.7684, -86.1581),
    ("detroit", "mi"): (42.3314, -83.0458),
    ("detroit", "michigan"): (42.3314, -83.0458),
    ("memphis", "tn"): (35.1495, -90.0490),
    ("memphis", "tennessee"): (35.1495, -90.0490),
    ("nashville", "tn"): (36.1627, -86.7816),
    ("nashville", "tennessee"): (36.1627, -86.7816),
    ("chicago", "il"): (41.8781, -87.6298),
    ("chicago", "illinois"): (41.8781, -87.6298),
    ("pittsburgh", "pa"): (40.4406, -79.9959),
    ("pittsburgh", "pennsylvania"): (40.4406, -79.9959),
    ("louisville", "ky"): (38.2527, -85.7585),
    ("louisville", "kentucky"): (38.2527, -85.7585),
    ("baltimore", "md"): (39.2904, -76.6122),
    ("baltimore", "maryland"): (39.2904, -76.6122),
    ("milwaukee", "wi"): (43.0389, -87.9065),
    ("milwaukee", "wisconsin"): (43.0389, -87.9065),
    ("las vegas", "nv"): (36.1699, -115.1398),
    ("las vegas", "nevada"): (36.1699, -115.1398),
    ("portland", "or"): (45.5152, -122.6784),
    ("portland", "oregon"): (45.5152, -122.6784),
    ("oklahoma city", "ok"): (35.4676, -97.5164),
    ("oklahoma city", "oklahoma"): (35.4676, -97.5164),
    ("new orleans", "la"): (29.9511, -90.0715),
    ("new orleans", "louisiana"): (29.9511, -90.0715),
    ("cleveland", "oh"): (41.4993, -81.6944),
    ("cleveland", "ohio"): (41.4993, -81.6944),
    ("cincinnati", "oh"): (39.1031, -84.5120),
    ("cincinnati", "ohio"): (39.1031, -84.5120),
    ("st louis", "mo"): (38.6270, -90.1994),
    ("st louis", "missouri"): (38.6270, -90.1994),
    ("saint louis", "mo"): (38.6270, -90.1994),
    ("saint louis", "missouri"): (38.6270, -90.1994),
    ("raleigh", "nc"): (35.7796, -78.6382),
    ("raleigh", "north carolina"): (35.7796, -78.6382),
    ("washington", "dc"): (38.9072, -77.0369),
    ("washington", "d.c."): (38.9072, -77.0369),
    ("washington dc", "dc"): (38.9072, -77.0369),
}


def geocode_city(city: str, state: str, use_api: bool = False) -> Optional[Tuple[float, float]]:
    """
    Convert city and state name to latitude and longitude.

    Args:
        city: City name (e.g., "Dallas", "San Antonio")
        state: State name or abbreviation (e.g., "TX", "Texas")
        use_api: If True, attempt to use geopy API. If False, use only fallback database.

    Returns:
        Tuple of (latitude, longitude) or None if not found

    Examples:
        >>> geocode_city("Dallas", "TX")
        (32.7767, -96.7970)

        >>> geocode_city("Atlanta", "Georgia")
        (33.7490, -84.3880)
    """
    # Normalize inputs
    city_lower = city.lower().strip()
    state_lower = state.lower().strip()

    # Try fallback database first
    key = (city_lower, state_lower)
    if key in US_CITIES:
        return US_CITIES[key]

    # If use_api is True, try geopy
    if use_api:
        try:
            from geopy.geocoders import Nominatim

            geolocator = Nominatim(user_agent="zurvan-product-delivery")
            location = geolocator.geocode(f"{city}, {state}, USA")
            if location:
                return (location.latitude, location.longitude)
        except ImportError:
            print("[Geocoding] geopy not installed. Install with: pip install geopy")
        except Exception as e:
            print(f"[Geocoding] Error using geopy: {e}")

    # Not found
    return None


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate that coordinates are reasonable US values.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        True if coordinates are within US bounds, False otherwise
    """
    # US rough bounds: lat 25-50, lon -125 to -65
    return 25 <= lat <= 50 and -125 <= lon <= -65
