from typing import Dict
from anthropic import Anthropic
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class AIService:
    """Claude AI integration for message enhancement"""
    
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def enhance_message(
        self, 
        base_message: str, 
        context: str, 
        user_comment: str,
        username: str
    ) -> Dict:
        """Use Claude to personalize/enhance the automated message"""
        
        prompt = f"""You are helping personalize an automated Instagram DM response.

Base message template: {base_message}

Business context: {context}

User's comment: "{user_comment}" by @{username}

Task: Enhance the base message to be more personalized and engaging while:
1. Keeping the core information from the base message
2. Acknowledging their specific comment naturally
3. Maintaining a friendly, conversational tone
4. Keeping it concise (under 500 characters)
5. Not being overly salesy

Return only the enhanced message text, nothing else."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            enhanced_text = message.content[0].text.strip()
            
            return {
                "success": True,
                "enhanced_message": enhanced_text,
                "original_message": base_message
            }
        except Exception as e:
            logger.error(f"AI enhancement failed: {str(e)}")
            return {
                "success": False,
                "enhanced_message": base_message,  # Fallback to original
                "error": str(e)
            }

