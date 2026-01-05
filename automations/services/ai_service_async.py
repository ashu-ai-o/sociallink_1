import httpx
import asyncio
from typing import Dict, List, Optional, Tuple
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
import logging

from core import settings

logger = logging.getLogger(__name__)


class AIServiceAsync:
    """
    Fully async AI service
    All API calls are non-blocking
    Handles 100+ concurrent AI requests
    """
    
    def __init__(self):
        self.openrouter_client = httpx.AsyncClient(
            base_url='https://openrouter.ai/api/v1',
            headers={
                'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
                'HTTP-Referer': 'https://linkplease.co',
            },
            timeout=60.0,
            limits=httpx.Limits(max_connections=50)
        )
        
        self.anthropic_client = AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        
        self.openai_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY
        )
    
    async def enhance_dm_message(
        self,
        base_message: str,
        business_context: str,
        user_comment: str,
        username: str,
        preferred_provider: str = 'openrouter'
    ) -> Dict:
        """
        Enhance DM message with AI (fully async)
        Tries multiple providers with automatic fallback
        """
        prompt = f"""Enhance this Instagram DM:

BASE: {base_message}
CONTEXT: {business_context}
COMMENT: "{user_comment}" by @{username}

Make it personal, friendly, under 500 chars. Return only the enhanced message."""

        # Try providers in order
        providers = [
            (preferred_provider, self._generate_with_preferred),
            ('openrouter', self._generate_openrouter),
            ('anthropic', self._generate_anthropic),
            ('openai', self._generate_openai),
        ]
        
        for provider_name, generate_func in providers:
            try:
                result = await generate_func(prompt)
                return {
                    'success': True,
                    'enhanced_message': result,
                    'original_message': base_message,
                    'provider_used': provider_name,
                    'model_used': 'auto',
                }
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        # All failed, return original
        return {
            'success': False,
            'enhanced_message': base_message,
            'error': 'All providers failed'
        }
    
    async def _generate_openrouter(self, prompt: str) -> str:
        """Generate with OpenRouter (async)"""
        response = await self.openrouter_client.post(
            '/chat/completions',
            json={
                'model': 'anthropic/claude-3.5-sonnet',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 400,
            }
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    
    async def _generate_anthropic(self, prompt: str) -> str:
        """Generate with Anthropic (async)"""
        message = await self.anthropic_client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=400,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return message.content[0].text
    
    async def _generate_openai(self, prompt: str) -> str:
        """Generate with OpenAI (async)"""
        response = await self.openai_client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=400,
        )
        return response.choices[0].message.content
    
    async def _generate_with_preferred(self, prompt: str) -> str:
        """Route to preferred provider"""
        return await self._generate_openrouter(prompt)
    
    async def close(self):
        """Close all clients"""
        await self.openrouter_client.aclose()