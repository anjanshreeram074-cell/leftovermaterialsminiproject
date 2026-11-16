# BuildBack — Vercel Serverless Function: Calculator API
# Pure Python - no Django required

import json
import os
from decimal import Decimal
from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance between two points in km"""
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371

def estimate_savings(params):
    """Calculate transport cost and savings"""
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

    return {
        'distance_km': float(round(dist_km, 2)),
        'transport_charge': float(round(transport_charge, 2)),
        'material_cost': float(round(material_cost, 2)),
        'total_purchase_cost': float(round(total_cost, 2)),
        'savings_amount': float(round(savings, 2)),
        'savings_percentage': float(round(savings_pct, 1)),
        'verdict': "Worth buying" if savings > 0 else "Not worth it",
        'is_worth_it': bool(savings > 0)
    }

def handler(request, response):
    """Vercel Serverless Function Handler"""
    # Set CORS headers
    response.set_header('Access-Control-Allow-Origin', '*')
    response.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.set_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    if request.method == 'OPTIONS':
        return response.status(200).end()

    try:
        # Get JSON body
        body = request.body
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        data = json.loads(body) if isinstance(body, str) else body

        if not data:
            return response.status(400).json({'error': 'No data provided'})

        # Calculate distance if not provided
        if 'distance_km' not in data:
            data['distance_km'] = 0

        result = estimate_savings(data)
        return response.status(200).json(result)

    except Exception as e:
        return response.status(500).json({'error': str(e), 'type': 'server_error'})