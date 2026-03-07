import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import InstagramAccount
import requests

a = InstagramAccount.objects.first()
print("connection_method:", a.connection_method)
print("instagram_user_id:", a.instagram_user_id)

# Test the fixed posts endpoint call
r = requests.get(
    "https://graph.instagram.com/v25.0/me/media",
    params={
        "access_token": a.access_token,
        "fields": "id,caption,media_type,thumbnail_url,media_url,timestamp,permalink",
        "limit": 20,
    },
    timeout=15
)
data = r.json()
if "error" in data:
    print("ERROR:", data["error"])
else:
    posts = data.get("data", [])
    print("Got posts:", len(posts))
    for p in posts:
        cap = (p.get("caption") or "")[:50]
        print("  id=%s caption=%s" % (p["id"], repr(cap)))
