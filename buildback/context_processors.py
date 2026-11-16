from django.conf import settings

def google_maps_key(request):
    return {'google_maps_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', '')}