from django.core.cache import cache
from django.http import JsonResponse
import time

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Skip rate limiting for non-API routes and authentication endpoints
        if not request.path.startswith('/api/') or request.path in ['/api/register', '/api/login']:
            return self.get_response(request)
        
        if request.user.is_authenticated:
            user_id = request.user.id
            cache_key = f"rate_limit_{user_id}"
            
            # Get current request count and timestamp
            current = cache.get(cache_key, {'count': 0, 'start_time': time.time()})
            
            # Reset if minute has passed
            if time.time() - current['start_time'] > 60:
                current = {'count': 0, 'start_time': time.time()}
            
            # Check if rate limit exceeded
            if current['count'] >= 60:
                return JsonResponse({
                    "error": {
                        "code": "RATE_LIMIT",
                        "message": "Rate limit exceeded"
                    }
                }, status=429)
            
            # Increment count
            current['count'] += 1
            cache.set(cache_key, current, 60)  # Store for 60 seconds
            
        return self.get_response(request)