import httpx
import asyncio
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class InstagramServiceAsync:
    """
    Fully async Instagram Graph API client
    Uses httpx for async HTTP requests
    Handles 1000s of concurrent requests
    """
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = 'https://graph.facebook.com/v21.0'
        
        # Create async HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            )
        )
    
    async def send_dm(
        self,
        recipient_id: str,
        message: str,
        buttons: List[Dict] = None
    ) -> Dict:
        """Send DM asynchronously"""
        url = f"{self.base_url}/me/messages"
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message}
        }
        
        if buttons:
            quick_replies = []
            for button in buttons:
                quick_replies.append({
                    "content_type": "text",
                    "title": button['text'][:20],
                    "payload": button.get('url', '')
                })
            payload["message"]["quick_replies"] = quick_replies
        
        params = {"access_token": self.access_token}
        
        try:
            response = await self.client.post(url, json=payload, params=params)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send DM: {e.response.status_code}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"DM send error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def check_if_following(
        self,
        instagram_account_id: str,
        user_id: str
    ) -> bool:
        """Check if user follows account (async)"""
        url = f"{self.base_url}/{instagram_account_id}"
        params = {
            "fields": "followers{id}",
            "access_token": self.access_token
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            followers = response.json().get('followers', {}).get('data', [])
            return any(f['id'] == user_id for f in followers)
        except Exception as e:
            logger.error(f"Follow check error: {str(e)}")
            return False
    
    async def get_comments(self, post_id: str) -> List[Dict]:
        """Get comments on a post (async)"""
        url = f"{self.base_url}/{post_id}/comments"
        params = {
            "fields": "id,text,username,from,timestamp",
            "access_token": self.access_token,
            "limit": 100
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Comments fetch error: {str(e)}")
            return []
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
