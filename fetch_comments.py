import os, django, asyncio
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import InstagramAccount
from automations.services.instagram_service_async import InstagramServiceAsync

async def test_fetch():
    account = await InstagramAccount.objects.aget(username="wanderwithraconz")
    service = InstagramServiceAsync(account.access_token, connection_method=account.connection_method)
    
    post_id = "18148423327459502"
    print(f"Fetching comments for post {post_id}...")
    comments = await service.get_comments(post_id)
    print(f"Found {len(comments)} comments.")
    for c in comments:
        print(f"  {c['id']} | @{c.get('username','?')} | {c.get('text','')} | from_id={c.get('from',{}).get('id','?')}")
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_fetch())
