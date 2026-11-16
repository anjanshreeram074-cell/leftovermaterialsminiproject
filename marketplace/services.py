import requests
from django.conf import settings
from decimal import Decimal
from math import radians, cos, sin, asin, sqrt
import datetime
from .models import DistanceCache

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers.
    return c * r

def get_road_distance(origin_lat, origin_lng, dest_lat, dest_lng):
    """
    Get road distance from Google Distance Matrix API with caching.
    Coords are rounded to 4 decimal places for caching (~11m precision).
    """
    o_lat = round(Decimal(origin_lat), 4)
    o_lng = round(Decimal(origin_lng), 4)
    d_lat = round(Decimal(dest_lat), 4)
    d_lng = round(Decimal(dest_lng), 4)

    # Check cache
    cache = DistanceCache.objects.filter(
        origin_lat=o_lat, origin_lng=o_lng,
        dest_lat=d_lat, dest_lng=d_lng,
        expires_at__gt=datetime.datetime.now()
    ).first()

    if cache:
        return {'distance_km': float(cache.km), 'duration_mins': cache.minutes}

    # API Call
    api_key = settings.GOOGLE_MAPS_API_KEY
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={o_lat},{o_lng}&destinations={d_lat},{d_lng}&key={api_key}"

    try:
        response = requests.get(url).json()
        if response['status'] == 'OK':
            element = response['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                dist_km = element['distance']['value'] / 1000.0
                dur_mins = int(element['duration']['value'] / 60)

                # Save to cache
                DistanceCache.objects.create(
                    origin_lat=o_lat, origin_lng=o_lng,
                    dest_lat=d_lat, dest_lng=d_lng,
                    km=dist_km,
                    minutes=dur_mins,
                    expires_at=datetime.datetime.now() + datetime.timedelta(days=7)
                )
                return {'distance_km': dist_km, 'duration_mins': dur_mins}
    except Exception as e:
        print(f"Distance API Error: {e}")

    # Fallback to Haversine if API fails
    return {'distance_km': haversine(o_lng, o_lat, d_lng, d_lat), 'duration_mins': 0}

def estimate_savings(params):
    """
    Calculate transport cost and savings.
    Inputs: quantity, vehicle_rate, min_fare, selling_price, new_market_price, distance_km
    """
    qty = Decimal(params.get('quantity', 0))
    rate = Decimal(params.get('vehicle_rate', 0))
    min_fare = Decimal(params.get('min_fare', 0))
    selling_price = Decimal(params.get('selling_price', 0))
    new_market_price = Decimal(params.get('new_market_price', 0))
    dist_km = Decimal(params.get('distance_km', 0))

    transport_charge = max(min_fare, dist_km * rate)
    material_cost = qty * selling_price
    total_cost = material_cost + transport_charge

    new_total_cost = qty * new_market_price
    savings = new_total_cost - total_cost
    savings_pct = (savings / new_total_cost * 100) if new_total_cost > 0 else 0

    worth_it = savings > 0

    return {
        'distance_km': float(round(dist_km, 2)),
        'transport_charge': float(round(transport_charge, 2)),
        'material_cost': float(round(material_cost, 2)),
        'total_purchase_cost': float(round(total_cost, 2)),
        'savings_amount': float(round(savings, 2)),
        'savings_percentage': float(round(savings_pct, 1)),
        'verdict': "Worth buying" if worth_it else "Not worth it",
        'is_worth_it': worth_it
    }
