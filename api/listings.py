# BuildBack — Vercel Serverless Function: Listings API (Proxy)
# Proxies requests to your actual backend (Railway/Render/Fly.io)

import os
import json
import requests
from urllib.parse import urlencode

BACKEND_URL = os.environ.get('BACKEND_API_URL', 'https://your-backend.up.railway.app')

def handler(request, response):
    # CORS headers
    response.set_header('Access-Control-Allow-Origin', '*')
    response.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.set_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    if request.method == 'OPTIONS':
        return response.status(200).end()

    path = request.path.replace('/api/listings', '')
    if not path:
        path = '/'

    # Forward query params
    query = ''
    if request.query:
        query = '?' + urlencode(request.query)

    url = f"{BACKEND_URL}/api/listings{path}{query}"

    try:
        if request.method == 'GET':
            resp = requests.get(url, timeout=10)
        elif request.method == 'POST':
            resp = requests.post(url, json=request.get_json(), timeout=10)
        else:
            return response.status(405).json({'error': 'Method not allowed'})

        return response.status(resp.status_code).json(resp.json())

    except requests.exceptions.RequestException as e:
        return response.status(502).json({'error': 'Backend unavailable', 'detail': str(e)})
    except Exception as e:
        return response.status(500).json({'error': str(e)})