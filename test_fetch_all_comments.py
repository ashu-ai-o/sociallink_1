import os
import sys
import requests
import json
import django

project_root = r'e:\linkautomation_for_social'
if project_root not in sys.path:
    sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import InstagramAccount

account = InstagramAccount.objects.get(username='wanderwithraconz', is_active=True)
ACCESS_TOKEN = account.access_token
IG_USER_ID = account.platform_id

print(f"Fetching posts for {IG_USER_ID}...")
url = f"https://graph.instagram.com/v25.0/{IG_USER_ID}/media"
params = {
    'access_token': ACCESS_TOKEN,
    'fields': 'id,caption,media_type,comments_count'
}

response = requests.get(url, params=params)
media_data = response.json()

if not response.ok:
    print("Error fetching media:")
    print(json.dumps(media_data, indent=2))
    sys.exit(1)

posts = media_data.get('data', [])
print(f"Found {len(posts)} posts. Checking comments...")

found_any = False
for post in posts[:5]:
    post_id = post['id']
    count = post.get('comments_count', 0)
    print(f"\nPost {post_id} - Comment Count on Instagram: {count}")
    
    url_comments = f"https://graph.instagram.com/v25.0/{post_id}/comments"
    params_comments = {
        'access_token': ACCESS_TOKEN,
        'fields': 'id,text,username,timestamp'
    }
    resp_comments = requests.get(url_comments, params=params_comments)
    c_data = resp_comments.json()
    items = c_data.get('data', [])
    print(f"-> API fetched {len(items)} comments.")
    if items:
        found_any = True
        for item in items:
            print(f"   - {item.get('text')} (by {item.get('username', 'unknown')})")
            
if not found_any:
    print("\nCould not fetch ANY comments via API across the last 5 posts.")
