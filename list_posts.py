import os, django, asyncio
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import InstagramAccount
from automations.services.instagram_service_async import InstagramServiceAsync

async def list_posts():
    account = await InstagramAccount.objects.aget(username="wanderwithraconz")
    service = InstagramServiceAsync(account.access_token, connection_method=account.connection_method)
    
    # Try fetching media
    url = f"{service.base_url}/me/media"
    params = {"access_token": service.access_token, "fields": "id,caption,permalink"}
    resp = await service.client.get(url, params=params)
    if resp.status_code == 200:
        media = resp.json().get('data', [])
        print(f"Found {len(media)} posts for @wanderwithraconz:")
        for m in media:
            print(f"  ID: {m['id']} | Caption: {m.get('caption', 'NO CAPTION')[:50]} | {m.get('permalink')}")
    else:
        print(f"Failed to fetch posts: {resp.status_code} - {resp.text}")
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(list_posts())
