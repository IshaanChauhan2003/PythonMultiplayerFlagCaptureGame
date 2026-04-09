from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random
import string
from .game_manager import game_manager

@csrf_exempt
def create_room(request):
    if request.method == 'POST':
        room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        passcode = ''.join(random.choices(string.digits, k=4))
        
        # Get wall data from request
        try:
            data = json.loads(request.body)
            walls = data.get('walls', [])
        except:
            walls = []
        
        game_manager.create_room(room_id, passcode, walls)
        
        return JsonResponse({
            'room_id': room_id,
            'passcode': passcode,
            'status': 'created'
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def join_room(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        room_id = data.get('room_id')
        passcode = data.get('passcode')
        
        success = game_manager.validate_room(room_id, passcode)
        
        if success:
            return JsonResponse({'status': 'valid', 'room_id': room_id})
        return JsonResponse({'error': 'Invalid room or passcode'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
