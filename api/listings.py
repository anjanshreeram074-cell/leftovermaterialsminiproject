# BuildBack — Vercel Serverless Function: Listings API Proxy
# Proxies requests to your main backend (Railway/Render/Fly.io)

import os
import json
import requests
from urllib.parse import urlencode

BACKEND_URL = os.environ.get('BACKEND_API_URL', 'https://your-backend.up.railway.app')

def handler(request, response):
    """Vercel Serverless Function Handler"""
    # Set CORS headers
    response.set_header('Access-Control-Allow-Origin', '*')
    response.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.set_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    if request.method == 'OPTIONS':
        return response.status(200).end()

    try:
        # Extract path after /api/listings
        path = request.path.replace('/api/listings', '')
        if not path:
            path = '/'

        # Build query string
        query = ''
        if request.query:
            query = '?' + urlencode(request.query)

        url = f"{BACKEND_URL}/api/listings{path}{query}"

        # Forward headers
        headers = {}
        for key, value in request.headers.items():
            if key.lower() in ['authorization', 'content-type', 'x-csrftoken', 'x-requested-with']:
                headers[key] = value

        # Get request body
        body = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            body = request.body
            if isinstance(body, bytes):
                body = body.decode('utf-8')

        # Forward request
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=body,
            params=request.query if request.method == 'GET' else None,
            timeout=15
        )

        # Return response
        response.set_header('Content-Type', 'application/json')
        return response.status(resp.status_code).json(resp.json())

    except requests.exceptions.Timeout:
        return response.status(504).json({'error': 'Backend timeout'})
    except requests.exceptions.ConnectionError:
        return response.status(502).json({'error': 'Backend unavailable'})
    except Exception as e:
        return response.status(500).json({'error': str(e)})