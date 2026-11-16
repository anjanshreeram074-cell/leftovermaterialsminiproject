from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .services import estimate_savings

@csrf_exempt
def calculate_estimate(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        result = estimate_savings(data)
        return JsonResponse(result)
    return JsonResponse({'error': 'Invalid request'}, status=400)
