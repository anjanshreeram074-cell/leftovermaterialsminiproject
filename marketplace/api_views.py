# BuildBack — API Views for Vercel Proxy
# REST API endpoints that Vercel serverless functions can proxy to

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
import json
import math

from .models import Material, MaterialImage, Location
from .services import get_road_distance
from .forms import MaterialForm, LocationForm


def serialize_material(material, request=None):
    """Convert Material object to dict for JSON response"""
    main_image = material.images.first()
    location = material.location_set.first()

    return {
        'id': material.id,
        'name': material.name,
        'category': material.category,
        'category_display': material.get_category_display(),
        'quantity': float(material.quantity),
        'unit': material.unit,
        'original_price': float(material.original_price),
        'selling_price': float(material.selling_price),
        'condition': material.condition,
        'condition_display': material.get_condition_display(),
        'status': material.status,
        'status_display': material.get_status_display(),
        'created_at': material.created_at.isoformat(),
        'seller': {
            'id': material.seller.id,
            'username': material.seller.username,
            'phone': material.seller.phone,
            'role': material.seller.role,
        } if material.seller else None,
        'image': main_image.image_url if main_image else None,
        'images': [{'url': img.image_url, 'position': img.position} for img in material.images.all()],
        'location': {
            'lat': float(location.lat),
            'lng': float(location.lng),
            'address': location.address,
        } if location else None,
    }


def api_listings(request):
    """GET /api/listings/ - List materials with filters"""
    materials = Material.objects.filter(status='available').select_related('seller').prefetch_related('images', 'location_set')

    # Search
    q = request.GET.get('q', '')
    if q:
        materials = materials.filter(Q(name__icontains=q) | Q(category__icontains=q))

    # Category filter
    cat = request.GET.get('category')
    if cat:
        materials = materials.filter(category=cat)

    # Sorting
    sort = request.GET.get('sort', '-created_at')
    if sort in ['selling_price', '-selling_price', '-created_at']:
        materials = materials.order_by(sort)
    else:
        materials = materials.order_by('-created_at')

    # Distance filter (bounding box)
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    if lat and lng:
        user_lat, user_lng = float(lat), float(lng)
        d_lat = 0.18
        d_lng = 0.18 / math.cos(math.radians(user_lat)) if user_lat != 0 else 0.18
        materials = materials.filter(
            location__lat__range=(user_lat - d_lat, user_lat + d_lat),
            location__lng__range=(user_lng - d_lng, user_lng + d_lng)
        )

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(materials, 12)
    page_obj = paginator.get_page(page)

    return JsonResponse({
        'results': [serialize_material(m) for m in page_obj],
        'pagination': {
            'page': page_obj.number,
            'pages': paginator.num_pages,
            'total': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        },
        'categories': [{'value': v, 'label': l} for v, l in Material.CATEGORY_CHOICES],
    })


def api_listing_detail(request, pk):
    """GET /api/listings/<pk>/ - Get single listing"""
    material = get_object_or_404(Material.objects.select_related('seller').prefetch_related('images', 'location_set'), pk=pk)
    return JsonResponse(serialize_material(material))


@csrf_exempt
@require_http_methods(['POST'])
def api_calculator_estimate(request):
    """POST /api/calculator/estimate/ - Calculate transport & savings"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # Calculate distance if coordinates provided
    if 'distance_km' not in data and all(k in data for k in ['origin_lat', 'origin_lng', 'dest_lat', 'dest_lng']):
        result = get_road_distance(data['origin_lat'], data['origin_lng'], data['dest_lat'], data['dest_lng'])
        data['distance_km'] = result['distance_km']

    # Import here to avoid circular imports
    from .services import estimate_savings
    result = estimate_savings(data)
    return JsonResponse(result)


@login_required
@csrf_exempt
def api_my_listings(request):
    """GET /api/my-listings/ - List user's own listings"""
    materials = Material.objects.filter(seller=request.user).order_by('-created_at')
    return JsonResponse({
        'results': [serialize_material(m) for m in materials],
    })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_create_listing(request):
    """POST /api/listings/ - Create new listing"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # Create material
    material = Material.objects.create(
        seller=request.user,
        name=data.get('name', ''),
        category=data.get('category', 'other'),
        quantity=data.get('quantity', 0),
        unit=data.get('unit', 'units'),
        original_price=data.get('original_price', 0),
        selling_price=data.get('selling_price', 0),
        condition=data.get('condition', 'unused'),
        status='available',
    )

    # Create location
    if 'location' in data:
        Location.objects.create(
            owner_type='material',
            owner_id=material.id,
            lat=data['location']['lat'],
            lng=data['location']['lng'],
            address=data['location'].get('address', ''),
        )

    # Create images
    for i, img_url in enumerate(data.get('image_urls', [])):
        MaterialImage.objects.create(material=material, image_url=img_url, position=i)

    return JsonResponse(serialize_material(material), status=201)


@login_required
@csrf_exempt
@require_http_methods(['PUT', 'PATCH'])
def api_update_listing(request, pk):
    """PUT /api/listings/<pk>/ - Update listing"""
    material = get_object_or_404(Material, pk=pk, seller=request.user)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    for field in ['name', 'category', 'quantity', 'unit', 'original_price', 'selling_price', 'condition', 'status']:
        if field in data:
            setattr(material, field, data[field])
    material.save()

    # Update location
    if 'location' in data:
        Location.objects.update_or_create(
            owner_type='material', owner_id=material.id,
            defaults={'lat': data['location']['lat'], 'lng': data['location']['lng'], 'address': data['location'].get('address', '')}
        )

    # Update images
    if 'image_urls' in data:
        material.images.all().delete()
        for i, img_url in enumerate(data['image_urls']):
            MaterialImage.objects.create(material=material, image_url=img_url, position=i)

    return JsonResponse(serialize_material(material))


@login_required
@require_http_methods(['DELETE'])
def api_delete_listing(request, pk):
    """DELETE /api/listings/<pk>/ - Delete listing"""
    material = get_object_or_404(Material, pk=pk, seller=request.user)
    material.delete()
    return JsonResponse({'success': True})


@login_required
@require_http_methods(['POST'])
def api_mark_sold(request, pk):
    """POST /api/listings/<pk>/sold/ - Mark as sold"""
    material = get_object_or_404(Material, pk=pk, seller=request.user)
    material.status = 'sold'
    material.save()
    return JsonResponse(serialize_material(material))