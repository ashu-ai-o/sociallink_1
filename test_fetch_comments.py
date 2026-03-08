import os
import sys
import django
import requests
import json

project_root = r'e:\linkautomation_for_social'
if project_root not in sys.path:
    sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import InstagramAccount

try:
    account = InstagramAccount.objects.get(username='wanderwithraconz', is_active=True)
    ACCESS_TOKEN = account.access_token
    print(f"Loaded Token for: @{account.username}")
except InstagramAccount.DoesNotExist:
    print("Could not find the Instagram account 'wanderwithraconz'")
    sys.exit(1)

# Using the post ID from earlier tests
POST_ID = '18148423327459502'

print(f"\nFetching comments for Post: {POST_ID}...")
url = f"https://graph.instagram.com/v25.0/{POST_ID}/comments"
params = {
    'access_token': ACCESS_TOKEN,
    'fields': 'id,text,timestamp,from,user'
}

response = requests.get(url, params=params)
comment_data = response.json()

print("\n--- API Response ---")
print(json.dumps(comment_data, indent=2))

if response.ok:
    comments = comment_data.get('data', [])
    print(f"\nFound {len(comments)} visible comments.")
    if len(comments) == 0:
        print("\nWARNING: Returned 0 comments.")
        print("This confirms Standard Access (Development Mode) restrictions.")
else:
    print("\nAPI Request Failed!")
