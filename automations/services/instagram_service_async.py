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
    Instagram API client with comment reply support.
    Supports both connection methods:
      - instagram_platform: uses graph.instagram.com
      - facebook_graph:     uses graph.facebook.com
    """
    
    def __init__(self, access_token: str, connection_method: str = 'facebook_graph'):
        self.access_token = access_token
        self.connection_method = connection_method
        
        # Choose correct base URL based on connection method
        if connection_method == 'instagram_platform':
            self.base_url = 'https://graph.instagram.com/v25.0'
        else:
            self.base_url = 'https://graph.facebook.com/v25.0'
        
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
        buttons: List[Dict] = None,
        comment_id: str = None
    ) -> Dict:
        """Send DM to user.

        For comment-triggered DMs, pass comment_id so Instagram allows the
        message even if the user has never messaged the account before.
        """
        url = f"{self.base_url}/me/messages"

        # Instagram requires comment_id as recipient for comment-triggered DMs.
        # Using user id directly causes 400 unless the user messaged first.
        # If we only have comment_id (instagram_user_id starts with 'comment:'),
        # extract it and use comment_id as the recipient.
        if comment_id:
            recipient = {"comment_id": comment_id}
        elif recipient_id and recipient_id.startswith('comment:'):
            # Fallback: instagram_user_id holds the comment_id when 'from.id' was absent
            extracted_comment_id = recipient_id[len('comment:'):]
            recipient = {"comment_id": extracted_comment_id}
            logger.info(f"send_dm: using comment_id={extracted_comment_id!r} as recipient (no user_id available)")
        else:
            recipient = {"id": recipient_id}

        payload = {
            "recipient": recipient,
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
            if not response.is_success:
                try:
                    err_json = response.json()
                    err = err_json.get('error', {})
                    logger.error(
                        f"[send_dm] Failed HTTP {response.status_code}: "
                        f"code={err.get('code')} subcode={err.get('error_subcode')} "
                        f"type={err.get('type')} message={err.get('message')!r}"
                    )
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "error_code": err.get('code'),
                        "error_subcode": err.get('error_subcode'),
                        "details": response.text,
                    }
                except Exception:
                    logger.error(f"[send_dm] Failed HTTP {response.status_code}: {response.text[:500]}")
                return {"success": False, "error": f"HTTP {response.status_code}", "details": response.text}
            return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"[send_dm] DM send exception: {str(e)}")
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
        
        form_data = {
            "message": reply_message
        }
        
        params = {"access_token": self.access_token}
        
        try:
            response = await self.client.post(url, data=form_data, params=params)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"✓ Replied to comment {comment_id}")
            
            return {
                "success": True,
                "comment_id": data.get('id'),
                "data": data
            }
        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to reply to comment: {e.response.status_code} - {e.response.text}"
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
        """
        Get comments on a post (all pages).
        
        Uses the correct API endpoint based on connection_method:
        - instagram_platform → graph.instagram.com/{post_id}/comments
        - facebook_graph     → graph.facebook.com/{post_id}/comments
        """
        url = f"{self.base_url}/{post_id}/comments"
        params = {
            "fields": "id,text,username,from,timestamp",
            "access_token": self.access_token,
            "limit": 100
        }

        all_comments = []

        try:
            while url:
                response = await self.client.get(url, params=params)

                if not response.is_success:
                    logger.error(
                        f"[get_comments] API error for post {post_id}: "
                        f"HTTP {response.status_code} — {response.text}"
                    )
                    return all_comments

                data = response.json()

                if 'error' in data:
                    err = data['error']
                    logger.error(
                        f"[get_comments] Instagram API error for post {post_id}: "
                        f"code={err.get('code')} subcode={err.get('error_subcode')} "
                        f"message={err.get('message')} type={err.get('type')}"
                    )
                    return all_comments

                page_comments = data.get('data', [])
                all_comments.extend(page_comments)

                logger.info(
                    f"[get_comments] post={post_id} fetched {len(page_comments)} comments "
                    f"(total so far: {len(all_comments)})"
                )

                # Follow pagination cursor if there are more pages
                paging = data.get('paging', {})
                next_url = paging.get('next')
                if next_url:
                    # next_url contains the full URL with all params already embedded
                    url = next_url
                    params = {}  # params already in the next URL
                else:
                    break

        except Exception as e:
            logger.error(f"[get_comments] Exception fetching comments for post {post_id}: {str(e)}")

        return all_comments

    
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