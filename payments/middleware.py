"""
Token Usage Tracking Middleware
Automatically tracks and validates token usage for AI operations
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .models import UserSubscription


# class TokenUsageMiddleware(MiddlewareMixin):
#     """
#     Middleware to check and track token usage for API requests
#     """
    
#     # Endpoints that consume tokens
#     TOKEN_CONSUMING_ENDPOINTS = [
#         '/api/projects/create/',
#         '/api/projects/',  # POST requests (chat)
#     ]
    
#     def process_request(self, request):
#         """
#         Check if user has sufficient tokens before processing request
#         """
#         # Skip for non-authenticated users
#         if not request.user.is_authenticated:
#             return None
        
#         # Check if this endpoint consumes tokens
#         path = request.path
#         method = request.method
        
#         # Only check for token-consuming endpoints
#         is_token_endpoint = any(
#             path.startswith(endpoint) for endpoint in self.TOKEN_CONSUMING_ENDPOINTS
#         )
        
#         if not is_token_endpoint or method not in ['POST', 'PUT']:
#             return None
        
#         # Get user's subscription
#         try:
#             subscription = UserSubscription.objects.select_related('plan').get(
#                 user=request.user
#             )
#         except UserSubscription.DoesNotExist:
#             return JsonResponse({
#                 'error': 'No active subscription found',
#                 'code': 'NO_SUBSCRIPTION'
#             }, status=403)
        
#         # Check subscription status
#         if subscription.status not in ['active', 'trial']:
#             return JsonResponse({
#                 'error': f'Subscription is {subscription.status}',
#                 'code': 'INACTIVE_SUBSCRIPTION'
#             }, status=403)
        
#         # Estimate token usage (you can make this more sophisticated)
#         estimated_tokens = self._estimate_token_usage(request)
        
#         # Check if user can use tokens
#         can_use, reason = subscription.can_use_tokens(estimated_tokens)
        
#         if not can_use:
#             return JsonResponse({
#                 'error': reason,
#                 'code': 'INSUFFICIENT_TOKENS',
#                 'tokens_remaining': subscription.tokens_remaining,
#                 'tokens_required': estimated_tokens
#             }, status=429)  # Too Many Requests
        
#         # Store estimated tokens in request for later use
#         request.estimated_tokens = estimated_tokens
#         request.user_subscription = subscription
        
#         return None
    
#     # def process_response(self, request, response):
#     #     """
#     #     Track actual token usage after request is processed
#     #     This is called in the view after AI processing
#     #     """
#     #     return response



#     def process_response(self, request, response):
#         """
#         Track tokens - supports both automatic and manual tracking
#         """
#         # Skip if not a token-consuming request
#         if not hasattr(request, 'user_subscription'):
#             return response
        
#         # Skip if request failed
#         if response.status_code not in [200, 201]:
#             return response
        
#         subscription = request.user_subscription
        
#         # Method 1: Check if view manually set tokens on request
#         if hasattr(request, 'actual_tokens_used'):
#             tokens_used = request.actual_tokens_used
#             description = getattr(request, 'token_description', 'API request')
#             project_id = getattr(request, 'project_id', None)
            
#             subscription.consume_tokens(
#                 token_count=tokens_used,
#                 description=description
#             )
#             return response
        
#         # Method 2: Try to extract from response body
#         try:
#             if hasattr(response, 'data') and isinstance(response.data, dict):
#                 tokens_used = response.data.get('tokens_used')
#                 if tokens_used:
#                     subscription.consume_tokens(
#                         token_count=tokens_used,
#                         description='Automatic tracking from response'
#                     )
#         except Exception:
#             pass
        
#         return response
    
#     def _estimate_token_usage(self, request):
#         """
#         Estimate token usage based on request
#         This is a simple estimation - actual usage will be tracked in views
#         """
#         # Default estimate
#         base_tokens = 10
        
#         # Check request body size
#         if hasattr(request, 'body'):
#             body_size = len(request.body)
#             # Roughly 4 characters per token
#             estimated = body_size // 4
#             base_tokens = max(base_tokens, estimated)
        
#         # Check for image uploads (images consume more tokens)
#         if request.FILES:
#             base_tokens += 50
        
#         return min(base_tokens, 100)  # Cap initial estimate at 100


# def track_token_usage(user, tokens_used, description="", project_id=None, feature="", ai_model=""):
#     """
#     Helper function to track token usage
#     Call this from views after AI operations
    
#     Usage:
#         from apps.payments.middleware import track_token_usage
        
#         # After AI operation
#         success = track_token_usage(
#             user=request.user,
#             tokens_used=actual_tokens,
#             description="Project creation",
#             project_id=str(project.id),
#             feature="project_generation"
#         )
#     """
#     try:
#         subscription = UserSubscription.objects.get(user=user)
#         return subscription.consume_tokens(
#             token_count=tokens_used,
#             description=description
#         )
#     except UserSubscription.DoesNotExist:
#         return False


# def check_token_availability(user, required_tokens):
#     """
#     Helper function to check if user has sufficient tokens
    
#     Usage:
#         from apps.payments.middleware import check_token_availability
        
#         can_use, reason = check_token_availability(request.user, 50)
#         if not can_use:
#             return Response({'error': reason}, status=429)
#     """
#     try:
#         subscription = UserSubscription.objects.get(user=user)
#         return subscription.can_use_tokens(required_tokens)
#     except UserSubscription.DoesNotExist:
#         return False, "No active subscription"