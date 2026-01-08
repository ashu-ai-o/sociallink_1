"""
Unified OpenRouter AI Service - Async Version
Uses OpenRouter exclusively with multiple model fallbacks
"""

import httpx
import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AIServiceOpenRouter:
    """
    Unified OpenRouter AI service with automatic model fallback
    All models accessed through a single API gateway
    Handles 100+ concurrent AI requests
    """
    
    # Model fallback chain (in priority order)
    MODELS = [
        {
            'id': 'anthropic/claude-3.5-sonnet',
            'name': 'Claude 3.5 Sonnet',
            'max_tokens': 400,
            'cost': 'medium',
            'speed': 'fast'
        },
        {
            'id': 'anthropic/claude-3-haiku',
            'name': 'Claude 3 Haiku',
            'max_tokens': 400,
            'cost': 'low',
            'speed': 'very_fast'
        },
        {
            'id': 'openai/gpt-4-turbo',
            'name': 'GPT-4 Turbo',
            'max_tokens': 400,
            'cost': 'medium',
            'speed': 'fast'
        },
        {
            'id': 'openai/gpt-3.5-turbo',
            'name': 'GPT-3.5 Turbo',
            'max_tokens': 400,
            'cost': 'low',
            'speed': 'very_fast'
        },
        {
            'id': 'meta-llama/llama-3.1-70b-instruct',
            'name': 'Llama 3.1 70B',
            'max_tokens': 400,
            'cost': 'low',
            'speed': 'fast'
        },
    ]
    
    def __init__(self, api_key: str, site_url: str = 'https://linkplease.co'):
        """
        Initialize OpenRouter client
        
        Args:
            api_key: OpenRouter API key
            site_url: Your site URL (for OpenRouter attribution)
        """
        self.api_key = api_key
        self.base_url = 'https://openrouter.ai/api/v1'
        self.site_url = site_url
        
        # Create async HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'HTTP-Referer': self.site_url,
                'X-Title': 'LinkPlease Pro',
                'Content-Type': 'application/json',
            },
            timeout=60.0,
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=20
            )
        )
    
    async def enhance_dm_message(
        self,
        base_message: str,
        business_context: str,
        user_comment: str,
        username: str,
        models: List[str] = None
    ) -> Dict:
        """
        Enhance DM message with AI (fully async)
        Tries multiple models with automatic fallback
        
        Args:
            base_message: Template message to enhance
            business_context: Business/brand context
            user_comment: User's comment that triggered automation
            username: Instagram username
            models: Optional list of model IDs to try (uses default if None)
        
        Returns:
            Dict with success, enhanced_message, model_used, etc.
        """
        prompt = self._build_enhancement_prompt(
            base_message, 
            business_context, 
            user_comment, 
            username
        )
        
        # Use provided models or default fallback chain
        models_to_try = models or [m['id'] for m in self.MODELS]
        
        # Try each model in sequence
        for model_id in models_to_try:
            try:
                model_info = next((m for m in self.MODELS if m['id'] == model_id), None)
                model_name = model_info['name'] if model_info else model_id
                
                logger.info(f"Trying model: {model_name}")
                
                result = await self._generate(
                    prompt=prompt,
                    model=model_id,
                    max_tokens=model_info['max_tokens'] if model_info else 400
                )
                
                if result['success']:
                    logger.info(f"✓ Success with {model_name}")
                    return {
                        'success': True,
                        'enhanced_message': result['text'],
                        'original_message': base_message,
                        'model_used': model_id,
                        'model_name': model_name,
                        'provider': 'openrouter',
                        'timestamp': datetime.utcnow().isoformat(),
                    }
                else:
                    logger.warning(f"✗ {model_name} failed: {result.get('error')}")
                    
            except Exception as e:
                logger.warning(f"✗ Model {model_id} exception: {str(e)}")
                continue
        
        # All models failed, return original message
        logger.error("All models failed, using original message")
        return {
            'success': False,
            'enhanced_message': base_message,
            'original_message': base_message,
            'error': 'All AI models failed',
            'models_tried': models_to_try,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    async def _generate(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 400,
        temperature: float = 0.7
    ) -> Dict:
        """
        Generate text using OpenRouter
        
        Args:
            prompt: Text prompt
            model: Model ID (e.g., 'anthropic/claude-3.5-sonnet')
            max_tokens: Maximum tokens to generate
            temperature: Creativity (0.0-1.0)
        
        Returns:
            Dict with success flag and generated text or error
        """
        try:
            response = await self.client.post(
                '/chat/completions',
                json={
                    'model': model,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ],
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract generated text
            text = data['choices'][0]['message']['content'].strip()
            
            return {
                'success': True,
                'text': text,
                'model': model,
                'usage': data.get('usage', {}),
            }
            
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_detail = error_data.get('error', {}).get('message', error_detail)
            except:
                pass
            
            return {
                'success': False,
                'error': error_detail,
                'status_code': e.response.status_code,
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def _build_enhancement_prompt(
        self,
        base_message: str,
        business_context: str,
        user_comment: str,
        username: str
    ) -> str:
        """Build prompt for message enhancement"""
        return f"""You are an Instagram DM automation assistant. Enhance this automated message to be more personalized and engaging.

BASE MESSAGE TEMPLATE:
{base_message}

BUSINESS CONTEXT:
{business_context}

USER'S COMMENT:
"{user_comment}" by @{username}

INSTRUCTIONS:
1. Keep the core information from the base message
2. Acknowledge their specific comment naturally (don't just repeat it)
3. Use a friendly, conversational tone
4. Keep it concise (under 500 characters)
5. Don't be overly salesy or formal
6. Use the username naturally if appropriate

OUTPUT:
Return ONLY the enhanced message text, nothing else (no quotes, no explanation)."""
    
    async def generate_multiple(
        self,
        prompts: List[str],
        model: str = None,
        max_concurrent: int = 10
    ) -> List[Dict]:
        """
        Generate responses for multiple prompts concurrently
        
        Args:
            prompts: List of prompts to process
            model: Model to use (uses first in fallback chain if None)
            max_concurrent: Maximum concurrent requests
        
        Returns:
            List of result dictionaries
        """
        model = model or self.MODELS[0]['id']
        
        # Process in batches to avoid overwhelming the API
        results = []
        for i in range(0, len(prompts), max_concurrent):
            batch = prompts[i:i + max_concurrent]
            batch_results = await asyncio.gather(
                *[self._generate(prompt, model) for prompt in batch],
                return_exceptions=True
            )
            results.extend(batch_results)
        
        return results
    
    async def get_available_models(self) -> List[Dict]:
        """
        Get list of available models from OpenRouter
        
        Returns:
            List of model information dictionaries
        """
        try:
            response = await self.client.get('/models')
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except Exception as e:
            logger.error(f"Failed to fetch models: {str(e)}")
            return []
    
    async def close(self):
        """Close HTTP client and cleanup"""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# ============================================================================
# SYNCHRONOUS VERSION (for non-async contexts)
# ============================================================================

import requests
from typing import Dict, List


class AIServiceOpenRouterSync:
    """
    Synchronous version of OpenRouter AI service
    Use this in non-async contexts (like Django views without async support)
    """
    
    MODELS = AIServiceOpenRouter.MODELS
    
    def __init__(self, api_key: str, site_url: str = 'https://linkplease.co'):
        self.api_key = api_key
        self.base_url = 'https://openrouter.ai/api/v1'
        self.site_url = site_url
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'HTTP-Referer': self.site_url,
            'X-Title': 'LinkPlease Pro',
            'Content-Type': 'application/json',
        }
    
    def enhance_dm_message(
        self,
        base_message: str,
        business_context: str,
        user_comment: str,
        username: str,
        models: List[str] = None
    ) -> Dict:
        """Synchronous version of enhance_dm_message"""
        prompt = self._build_enhancement_prompt(
            base_message, business_context, user_comment, username
        )
        
        models_to_try = models or [m['id'] for m in self.MODELS]
        
        for model_id in models_to_try:
            try:
                model_info = next((m for m in self.MODELS if m['id'] == model_id), None)
                model_name = model_info['name'] if model_info else model_id
                
                result = self._generate(
                    prompt=prompt,
                    model=model_id,
                    max_tokens=model_info['max_tokens'] if model_info else 400
                )
                
                if result['success']:
                    return {
                        'success': True,
                        'enhanced_message': result['text'],
                        'original_message': base_message,
                        'model_used': model_id,
                        'model_name': model_name,
                        'provider': 'openrouter',
                    }
            except Exception as e:
                logger.warning(f"Model {model_id} failed: {str(e)}")
                continue
        
        return {
            'success': False,
            'enhanced_message': base_message,
            'error': 'All models failed'
        }
    
    def _generate(self, prompt: str, model: str, max_tokens: int = 400) -> Dict:
        """Synchronous generation"""
        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=self.headers,
                json={
                    'model': model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': max_tokens,
                },
                timeout=60
            )
            
            response.raise_for_status()
            data = response.json()
            text = data['choices'][0]['message']['content'].strip()
            
            return {'success': True, 'text': text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _build_enhancement_prompt(self, base_message: str, business_context: str,
                                   user_comment: str, username: str) -> str:
        """Same as async version"""
        return f"""You are an Instagram DM automation assistant. Enhance this automated message to be more personalized and engaging.

BASE MESSAGE TEMPLATE:
{base_message}

BUSINESS CONTEXT:
{business_context}

USER'S COMMENT:
"{user_comment}" by @{username}

INSTRUCTIONS:
1. Keep the core information from the base message
2. Acknowledge their specific comment naturally
3. Use a friendly, conversational tone
4. Keep it concise (under 500 characters)
5. Don't be overly salesy
6. Use the username naturally if appropriate

OUTPUT:
Return ONLY the enhanced message text, nothing else."""


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
# Async Usage (in Celery tasks, WebSocket consumers, etc.)
async def process_automation():
    async with AIServiceOpenRouter(api_key='your-key') as ai:
        result = await ai.enhance_dm_message(
            base_message="Thanks for your interest! Here's the link: {link}",
            business_context="We sell premium coffee subscriptions",
            user_comment="This looks amazing! Where can I buy?",
            username="coffee_lover_123"
        )
        
        if result['success']:
            print(f"Enhanced message: {result['enhanced_message']}")
            print(f"Used model: {result['model_name']}")
        else:
            print(f"Failed, using original: {result['enhanced_message']}")


# Sync Usage (in regular Django views)
def my_view(request):
    ai = AIServiceOpenRouterSync(api_key='your-key')
    result = ai.enhance_dm_message(
        base_message="Thanks for commenting!",
        business_context="Fitness coaching business",
        user_comment="Love this workout!",
        username="gym_enthusiast"
    )
    return JsonResponse(result)


# Batch Processing (100+ prompts concurrently)
async def process_batch():
    async with AIServiceOpenRouter(api_key='your-key') as ai:
        prompts = ["Prompt 1", "Prompt 2", ...] # 100+ prompts
        results = await ai.generate_multiple(
            prompts=prompts,
            max_concurrent=20  # Process 20 at a time
        )


# Custom Model Selection
async def use_specific_models():
    async with AIServiceOpenRouter(api_key='your-key') as ai:
        result = await ai.enhance_dm_message(
            base_message="...",
            business_context="...",
            user_comment="...",
            username="...",
            models=[
                'anthropic/claude-3.5-sonnet',  # Try this first
                'openai/gpt-4-turbo'             # Then this
            ]
        )
"""