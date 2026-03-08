import os, django, asyncio
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import InstagramAccount
from automations.services.instagram_service_async import InstagramServiceAsync

async def test_dm():
    account = await InstagramAccount.objects.aget(username="wanderwithraconz")
    service = InstagramServiceAsync(account.access_token, connection_method=account.connection_method)
    
    # Try to DM THEMSELVES (should be a valid ID even if not a "messageable" conversation yet)
    recipient_id = account.instagram_user_id
    print(f"Testing DM send to self ({recipient_id}) using method {account.connection_method}...")
    result = await service.send_dm(recipient_id, "Test automations message")
    
    print(f"Result: {result}")
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_dm())
