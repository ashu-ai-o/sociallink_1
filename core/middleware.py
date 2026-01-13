from django.core.cache import cache
from django.http import JsonResponse
import time


class RateLimitMiddleware:
    """
    Rate limit API requests per user
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for non-API requests
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Skip for authentication endpoints
        if request.path.startswith('/api/auth/'):
            return self.get_response(request)
        
        # Get user identifier
        if request.user.is_authenticated:
            user_id = str(request.user.id)
        else:
            # For anonymous users, use IP address
            user_id = self.get_client_ip(request)
        
        # Rate limit key
        rate_limit_key = f'rate_limit:{user_id}:{int(time.time() / 60)}'
        
        # Get current count
        count = cache.get(rate_limit_key, 0)
        
        # Limit: 100 requests per minute
        if count >= 100:
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again in a minute.'
            }, status=429)
        
        # Increment count
        cache.set(rate_limit_key, count + 1, 60)
        
        response = self.get_response(request)
        
        # Add rate limit headers
        response['X-RateLimit-Limit'] = '100'
        response['X-RateLimit-Remaining'] = str(100 - count - 1)
        response['X-RateLimit-Reset'] = str(int(time.time() / 60 + 1) * 60)
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
