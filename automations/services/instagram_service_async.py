"""
Instagram Service - WITH COMMENT REPLY FEATURE
Replies to comments publicly + sends DM privately
"""

import httpx
import asyncio
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class InstagramServiceAsync:
    """
    Instagram Graph API client with comment reply support
    """
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = 'https://graph.facebook.com/v21.0'
        
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
        """Send DM to user"""
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
    
    # ═══════════════════════════════════════════════════════════════
    # NEW FEATURE: Reply to Comment Publicly
    # ═══════════════════════════════════════════════════════════════
    
    async def reply_to_comment(
        self,
        comment_id: str,
        reply_message: str
    ) -> Dict:
        """
        Reply to a comment publicly on Instagram
        
        Args:
            comment_id: Instagram comment ID
            reply_message: Text to reply with
            
        Returns:
            {"success": True/False, "comment_id": "...", "error": "..."}
        """
        url = f"{self.base_url}/{comment_id}/replies"
        
        payload = {
            "message": reply_message
        }
        
        params = {"access_token": self.access_token}
        
        try:
            response = await self.client.post(url, json=payload, params=params)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"✓ Replied to comment {comment_id}")
            
            return {
                "success": True,
                "comment_id": data.get('id'),
                "data": data
            }
        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to reply to comment: {e.response.status_code}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Comment reply error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    # ═══════════════════════════════════════════════════════════════
    
    async def check_if_following(
        self,
        instagram_account_id: str,
        user_id: str
    ) -> bool:
        """Check if user follows account"""
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
        """Get comments on a post"""
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


# ═══════════════════════════════════════════════════════════════
# USAGE EXAMPLES
# ═══════════════════════════════════════════════════════════════

"""
# Example 1: Reply to comment + send DM

instagram_service = InstagramServiceAsync(access_token)

# Reply publicly
comment_reply = await instagram_service.reply_to_comment(
    comment_id="comment_123",
    reply_message="Thanks! 👋 Check your DM for the link!"
)

# Send DM privately
dm_result = await instagram_service.send_dm(
    recipient_id="user_456",
    message="Here's the link: https://shop.com/product"
)


# Example 2: Different reply messages

# Short acknowledgment
await instagram_service.reply_to_comment(
    comment_id="comment_123",
    reply_message="✅ Sent! Check your inbox"
)

# With emoji
await instagram_service.reply_to_comment(
    comment_id="comment_123",
    reply_message="🎉 Done! DMed you the link!"
)

# Encouraging others to comment
await instagram_service.reply_to_comment(
    comment_id="comment_123",
    reply_message="Link sent! 📩 Comment 'link please' to get yours!"
)
"""