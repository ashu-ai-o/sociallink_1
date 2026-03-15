"""
Gemini API Service - Async Version
Uses Google Gemini API via REST
Supports multi-key rotation via GeminiKeyPool
"""

import httpx
import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_key_pool = None

def _get_key_pool():
    """Return the global key pool singleton (lazy init)."""
    global _key_pool
    if _key_pool is None:
        from automations.services.gemini_key_pool import GeminiKeyPool
        _key_pool = GeminiKeyPool.from_settings()
    return _key_pool


class AIServiceGemini:
    """
    Unified Gemini AI service
    """
    
    MODELS = [
        {
            'id': 'gemini-1.5-flash',
            'name': 'Gemini 1.5 Flash',
            'max_tokens': 400,
            'cost': 'free',
            'speed': 'fast'
        }
    ]
    
    def __init__(self, api_key: Optional[str] = None, use_key_pool: bool = True):
        self._static_api_key = api_key
        self._use_key_pool = use_key_pool and api_key is None
        self.base_url = 'https://generativelanguage.googleapis.com/v1beta/models'

        self.client = httpx.AsyncClient(
            timeout=60.0,
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=20
            )
        )
    
    async def enhance_DmMessage(
        self,
        base_message: str,
        business_context: str,
        user_comment: str,
        username: str,
        models: Optional[List[str]] = None
    ) -> Dict:
        """Enhance DM message with Gemini"""
        prompt = self._build_enhancement_prompt(
            base_message, 
            business_context, 
            user_comment, 
            username
        )
        
        models_to_try = models or [m['id'] for m in self.MODELS]
        
        for model_id in models_to_try:
            try:
                model_info = next((m for m in self.MODELS if m['id'] == model_id), None)
                model_name = model_info['name'] if model_info else model_id
                
                logger.info(f"Trying Gemini model: {model_name}")
                
                result = await self._generate(
                    prompt=prompt,
                    model=str(model_id),
                    max_tokens=int(model_info['max_tokens']) if model_info else 400
                )
                
                if result['success']:
                    logger.info(f"✓ Success with {model_name}")
                    return {
                        'success': True,
                        'enhanced_message': result['text'],
                        'original_message': base_message,
                        'model_used': model_id,
                        'model_name': model_name,
                        'provider': 'gemini',
                        'timestamp': datetime.utcnow().isoformat(),
                    }
                else:
                    logger.warning(f"✗ {model_name} failed: {result.get('error')}")
                    status_code = result.get('status_code')
                    if status_code in [401, 403]:
                        logger.error(f"Critical API error {status_code}: Aborting model fallback.")
                        break
                    
            except Exception as e:
                logger.warning(f"✗ Model {model_id} exception: {str(e)}")
                continue
        
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
        if self._use_key_pool:
            api_key = await _get_key_pool().get_key()
        else:
            api_key = self._static_api_key or ''

        try:
            url = f"{self.base_url}/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                }
            }
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            try:
                text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            except (KeyError, IndexError):
                return {
                    'success': False,
                    'error': 'Unexpected response format from Gemini',
                    'response': data
                }

            return {
                'success': True,
                'text': text,
                'model': model,
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
    
    async def generate_multiple(self, prompts: List[str], model: Optional[str] = None, max_concurrent: int = 10) -> List[Dict]:
        actual_model = str(model) if model else str(self.MODELS[0]['id'])
        results = []
        for i in range(0, len(prompts), max_concurrent):
            batch = prompts[i:i + max_concurrent]
            batch_results = await asyncio.gather(
                *[self._generate(prompt, actual_model) for prompt in batch],
                return_exceptions=True
            )
            results.extend([res for res in batch_results if isinstance(res, dict)])
        return results
        
    async def close(self):
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
