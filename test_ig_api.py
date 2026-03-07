import os
import django
import asyncio
import httpx

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import InstagramAccount
from automations.models import AutomationTrigger

async def amain(act):
    base_url = 'https://graph.instagram.com/v25.0'
    
    # We need a real comment ID to test Comment Reply or Private Reply.
    # Let's see if we can get a comment from a post
    print("\n--- Fetching Comments ---")
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{base_url}/18148423327459502/comments",
            params={
                "fields": "id,text,username,from",
                "access_token": act.access_token
            }
        )
        comments = res.json().get("data", [])
        if not comments:
            print("No comments found. Raw response:")
            print(res.json())
            return
            
        print("Got comments:")
        for c in comments:
            print(f"  {c['id']} - {c.get('username')}: {c.get('text')}")
            
        c = comments[0]
        comment_id = c['id']
        
        print(f"\n--- Testing Private Reply via Comment ID ({comment_id}) ---")
        payload = {
            "recipient": {"comment_id": comment_id},
            "message": {"text": "Hello from private reply!"}
        }
        res2 = await client.post(
            f"{base_url}/me/messages",
            json=payload,
            params={"access_token": act.access_token}
        )
        print(res2.status_code)
        print(res2.text)

def main():
    act = InstagramAccount.objects.filter(is_active=True).first()
    if not act:
        print("No active accounts")
        return
    asyncio.run(amain(act))

if __name__ == '__main__':
    main()
