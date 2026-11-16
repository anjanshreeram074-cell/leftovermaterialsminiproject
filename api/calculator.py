# BuildBack — Vercel Serverless Function: Calculator API
# This is a standalone version that doesn't require Django

import json
import os
from decimal import Decimal
from math import radians, cos, sin, asin, sqrt
import requests

# Haversine fallback (same as services.py)
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371

def estimate_savings(params):
    """Pure Python calculator - no Django dependencies"""
    qty = Decimal(str(params.get('quantity', 0)))
    rate = Decimal(str(params.get('vehicle_rate', 0)))
    min_fare = Decimal(str(params.get('min_fare', 0)))
    selling_price = Decimal(str(params.get('selling_price', 0)))
    new_market_price = Decimal(str(params.get('new_market_price', 0)))
    dist_km = Decimal(str(params.get('distance_km', 0)))

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

# Vercel handler
def handler(request, response):
    if request.method != 'POST':
        return response.status(405).json({'error': 'Method not allowed'})

    try:
        data = request.get_json()
        if not data:
            return response.status(400).json({'error': 'Invalid JSON'})

        # If distance_km not provided, try to get from Google Distance Matrix
        if 'distance_km' not in data or not data['distance_km']:
            if 'origin_lat' in data and 'origin_lng' in data and 'dest_lat' in data and 'dest_lng' in data:
                api_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
                if api_key:
                    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={data['origin_lat']},{data['origin_lng']}&destinations={data['dest_lat']},{data['dest_lng']}&key={api_key}"
                    try:
                        resp = requests.get(url, timeout=5).json()
                        if resp['status'] == 'OK':
                            elem = resp['rows'][0]['elements'][0]
                            if elem['status'] == 'OK':
                                data['distance_km'] = elem['distance']['value'] / 1000.0
                    except Exception:
                        pass

                # Fallback to Haversine
                if 'distance_km' not in data:
                    data['distance_km'] = haversine(
                        data['origin_lng'], data['origin_lat'],
                        data['dest_lng'], data['dest_lat']
                    )

        result = estimate_savings(data)
        return response.status(200).json(result)

    except Exception as e:
        return response.status(500).json({'error': str(e)})