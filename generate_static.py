#!/usr/bin/env python
"""
BuildBack — Static Site Generator for Vercel
Generates static HTML from Django templates for frontend-only deployment.
Run: python generate_static.py
Output: ./static_build/
"""

import os
import sys
import shutil
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buildback.settings')
import django
django.setup()

from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import SafeString

# Static build directory
BUILD_DIR = Path(__file__).parent / 'static_build'
STATIC_DIR = BUILD_DIR / 'static'

# Mock URL resolver for static generation
def mock_url(name, *args, **kwargs):
    """Generate static URLs for Vercel deployment"""
    url_map = {
        'home': '/',
        'browse': '/browse/',
        'sell': '/sell/',
        'detail': f'/listing/{kwargs.get("pk", args[0] if args else "")}/',
        'my_listings': '/my-listings/',
        'edit_listing': f'/edit/{kwargs.get("pk", args[0] if args else "")}/',
        'delete_listing': f'/delete/{kwargs.get("pk", args[0] if args else "")}/',
        'mark_sold': f'/sold/{kwargs.get("pk", args[0] if args else "")}/',
        'register': '/register/',
        'login': '/login/',
        'logout': '/logout/',
        'calculate_estimate': '/api/calculator/',
    }
    return url_map.get(name, '#')

# Patch reverse for static generation
import django.urls.base
django.urls.base.reverse = mock_url

from marketplace.models import Material, MaterialImage, Location

# Static build directory
BUILD_DIR = Path(__file__).parent / 'static_build'
STATIC_DIR = BUILD_DIR / 'static'

def clean_build_dir():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)
    STATIC_DIR.mkdir(parents=True)

def copy_static_files():
    """Copy static files to build directory"""
    for static_root in settings.STATICFILES_DIRS:
        for item in Path(static_root).rglob('*'):
            if item.is_file():
                rel = item.relative_to(static_root)
                dest = STATIC_DIR / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

def render_template(template_name, context, output_path):
    """Render a Django template to static HTML"""
    html = render_to_string(template_name, context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)

class MockMaterial:
    """Mock material object with all template-accessible attributes"""
    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)
        # Add methods that templates might call
        self.get_condition_display = lambda: self.condition.capitalize()
        self.get_status_display = lambda: self.status.capitalize()

    def __getattr__(self, name):
        # Handle related objects
        if name == 'images':
            return MockManager(self._images)
        if name == 'location_set':
            return MockManager([self._location])
        return super().__getattr__(name)

class MockManager:
    """Mock queryset manager"""
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items

    def first(self):
        return self.items[0] if self.items else None

    def count(self):
        return len(self.items)

class MockLocation:
    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)

class MockUser:
    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)
        self.get_role_display = lambda: self.role.capitalize() if hasattr(self, 'role') else 'Buyer'

def build_pages():
    """Generate all static pages"""

    # Sample data for static generation
    sample_materials = [
        {
            'id': 1,
            'pk': 1,
            'name': 'Ceramic Floor Tiles',
            'category': 'tiles',
            'quantity': 150,
            'unit': 'sqft',
            'original_price': 45,
            'selling_price': 28,
            'condition': 'unused',
            'status': 'available',
            'created_at': '2025-01-15',
            'seller': MockUser({'username': 'builder_raj', 'phone': '9876543210', 'role': 'seller'}),
            '_images': [MockManager([])],  # Will be replaced
            '_location': MockLocation({'lat': 28.6139, 'lng': 77.2090, 'address': 'Delhi, India'}),
        },
        {
            'id': 2,
            'pk': 2,
            'name': 'OPC Cement 53 Grade',
            'category': 'cement',
            'quantity': 50,
            'unit': 'bags',
            'original_price': 380,
            'selling_price': 290,
            'condition': 'unused',
            'status': 'available',
            'created_at': '2025-01-14',
            'seller': MockUser({'username': 'cement_supplier', 'phone': '9123456789', 'role': 'seller'}),
            '_images': [MockManager([])],
            '_location': MockLocation({'lat': 28.7041, 'lng': 77.1025, 'address': 'Noida, India'}),
        },
    ]

    # Add images to materials
    sample_materials[0]['_images'] = [type('Image', (), {'image_url': 'https://res.cloudinary.com/demo/image/upload/v1/tiles.jpg', 'position': 0})()]
    sample_materials[1]['_images'] = [type('Image', (), {'image_url': 'https://res.cloudinary.com/demo/image/upload/v1/cement.jpg', 'position': 0})()]

    # Convert to mock objects
    mock_materials = [MockMaterial(m) for m in sample_materials]

    categories = [
        ('tiles', 'Tiles'), ('cement', 'Cement'), ('bricks', 'Bricks'),
        ('steel', 'Steel'), ('pipes', 'Pipes'), ('other', 'Other')
    ]

    # Common context
    base_context = {
        'google_maps_key': os.environ.get('GOOGLE_MAPS_API_KEY', ''),
        'categories': categories,
        'user': type('User', (), {'is_authenticated': False})(),
        'request': type('Request', (), {'resolver_match': type('Match', (), {'url_name': 'home'})()})(),
    }

    # 1. Home page
    print("Generating home page...")
    stats = {
        'listings': len(mock_materials),
        'sellers': 2,
        'radius': 20,
        'avg_savings': 25,
    }
    render_template('home.html', {**base_context, 'stats': stats, 'featured': mock_materials}, BUILD_DIR / 'index.html')

    # 2. Browse page
    print("Generating browse page...")
    class MockPageObj:
        object_list = mock_materials
        paginator = type('Paginator', (), {'count': len(mock_materials), 'num_pages': 1, 'page_range': [1]})()
        number = 1
        has_previous = False
        has_next = False
        previous_page_number = lambda: 1
        next_page_number = lambda: 1

    render_template('browse.html', {**base_context, 'page_obj': MockPageObj(), 'selected_cat': '', 'query': '', 'sort': '-created_at'}, BUILD_DIR / 'browse' / 'index.html')

    # 3. Sell page
    print("Generating sell page...")
    render_template('sell.html', {**base_context, 'form': None, 'loc_form': None, 'img_form': None, 'edit_mode': False}, BUILD_DIR / 'sell' / 'index.html')

    # 4. Listing detail pages
    print("Generating detail pages...")
    for material in mock_materials:
        render_template('detail.html', {**base_context, 'material': material, 'location': material._location, 'calc_defaults': {'vehicle_rate': 15, 'min_fare': 100}}, BUILD_DIR / 'listing' / str(material.id) / 'index.html')

    # 5. Auth pages
    print("Generating auth pages...")
    render_template('login.html', {**base_context, 'form': None}, BUILD_DIR / 'login' / 'index.html')
    render_template('register.html', {**base_context, 'form': None}, BUILD_DIR / 'register' / 'index.html')

    # 6. My listings
    print("Generating my-listings page...")
    render_template('my_listings.html', {**base_context, 'listings': []}, BUILD_DIR / 'my-listings' / 'index.html')

    print(f"✅ Static site generated in {BUILD_DIR}")

if __name__ == '__main__':
    clean_build_dir()
    copy_static_files()
    build_pages()
    print(f"\n🚀 Deploy to Vercel:")
    print(f"   vercel --prod {BUILD_DIR}")