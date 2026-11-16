from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import math
from .models import Material, MaterialImage, Location
from .forms import RegistrationForm, MaterialForm, LocationForm, ImageUploadForm
from .services import get_road_distance
from django.contrib.auth.forms import AuthenticationForm

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

def home(request):
    stats = {
        'listings': Material.objects.filter(status='available').count(),
        'sellers': Material.objects.filter(status='available').values('seller').distinct().count(),
        'radius': 20,
        'avg_savings': 25,
    }
    featured = Material.objects.filter(status='available').order_by('-created_at')[:4]
    return render(request, 'home.html', {'stats': stats, 'featured': featured})

def browse(request):
    materials = Material.objects.filter(status='available').select_related('seller').prefetch_related('images')

    q = request.GET.get('q', '')
    if q:
        materials = materials.filter(Q(name__icontains=q) | Q(category__icontains=q))

    cat = request.GET.get('category')
    if cat:
        materials = materials.filter(category=cat)

    sort = request.GET.get('sort', '-created_at')
    if sort in ['selling_price', '-selling_price']:
        materials = materials.order_by(sort)
    else:
        materials = materials.order_by('-created_at')

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

    paginator = Paginator(materials, 12)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    return render(request, 'browse.html', {
        'page_obj': page_obj,
        'categories': Material.CATEGORY_CHOICES,
        'selected_cat': cat,
        'query': q,
        'sort': sort,
    })

@login_required
def sell(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        loc_form = LocationForm(request.POST)
        img_form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid() and loc_form.is_valid():
            material = form.save(commit=False)
            material.seller = request.user
            material.save()

            loc = loc_form.save(commit=False)
            loc.owner_type = 'material'
            loc.owner_id = material.id
            loc.save()

            image_urls = request.POST.getlist('image_urls')
            for i, url in enumerate(image_urls):
                MaterialImage.objects.create(material=material, image_url=url, position=i)

            return redirect('detail', pk=material.pk)
    else:
        form = MaterialForm()
        loc_form = LocationForm()
        img_form = ImageUploadForm()

    return render(request, 'sell.html', {
        'form': form,
        'loc_form': loc_form,
        'img_form': img_form,
        'google_maps_key': getattr(request, 'google_maps_key', '')
    })

def detail(request, pk):
    material = get_object_or_404(Material.objects.select_related('seller').prefetch_related('images'), pk=pk)
    location = material.location_set.first()

    defaults = {
        'vehicle_rate': 15,
        'min_fare': 100,
    }
    return render(request, 'detail.html', {
        'material': material,
        'location': location,
        'google_maps_key': getattr(request, 'google_maps_key', ''),
        'calc_defaults': defaults
    })

@login_required
def my_listings(request):
    listings = Material.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'my_listings.html', {'listings': listings})

@login_required
def edit_listing(request, pk):
    material = get_object_or_404(Material, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            return redirect('my_listings')
    else:
        form = MaterialForm(instance=material)
    return render(request, 'sell.html', {'form': form, 'edit_mode': True, 'material': material})

@login_required
def delete_listing(request, pk):
    material = get_object_or_404(Material, pk=pk, seller=request.user)
    if request.method == 'POST':
        material.delete()
        return redirect('my_listings')
    return render(request, 'partials/delete_confirm.html', {'material': material})

@login_required
def mark_sold(request, pk):
    material = get_object_or_404(Material, pk=pk, seller=request.user)
    material.status = 'sold'
    material.save()
    return redirect('my_listings')