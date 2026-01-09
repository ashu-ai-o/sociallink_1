# 🔐 Complete Instagram OAuth Setup Guide

## 📋 Overview

This guide walks you through setting up Instagram authentication for LinkPlease Pro using the official Meta API.

---

## 🎯 Prerequisites

1. **Instagram Account Requirements:**
   - ✅ Must be Business or Creator account (Personal accounts won't work)
   - ✅ Must be connected to a Facebook Page
   - ✅ Page must be published (not in draft mode)

2. **Developer Access:**
   - Meta Developer account
   - Facebook App created
   - App in Development mode (for testing)

---

## 🚀 Step 1: Create Meta Developer App

### 1.1 Go to Meta for Developers

Visit: https://developers.facebook.com/

### 1.2 Create New App

1. Click **"Create App"**
2. Select **"Business"** as app type
3. Fill in details:
   - **App Name**: LinkPlease Pro
   - **App Contact Email**: your-email@example.com
   - **Business Account**: (Optional) Select or create

### 1.3 Add Instagram Product

1. In your app dashboard, click **"Add Product"**
2. Find **"Instagram"** and click **"Set Up"**
3. Find **"Messenger"** and click **"Set Up"** (required for DMs)

### 1.4 Configure App Settings

**Basic Settings:**
- App Domain: `localhost` (for development)
- Privacy Policy URL: Your privacy policy
- Terms of Service URL: Your terms
- App Icon: Upload your logo

---

## 🔑 Step 2: Get API Credentials

### 2.1 Get App ID and Secret

1. Go to **Settings > Basic**
2. Copy:
   - **App ID** (this is your FACEBOOK_APP_ID)
   - **App Secret** (this is your FACEBOOK_APP_SECRET)
   - Click "Show" to reveal secret

### 2.2 Add to Backend `.env`

```env
# Instagram OAuth
FACEBOOK_APP_ID=1234567890123456
FACEBOOK_APP_SECRET=abc123def456ghi789jkl012mno345pq
FRONTEND_URL=http://localhost:3000
```

---

## 🔧 Step 3: Configure OAuth Settings

### 3.1 Add OAuth Redirect URIs

1. Go to **Products > Facebook Login > Settings**
2. Add **Valid OAuth Redirect URIs**:
   ```
   http://localhost:3000/auth/instagram/callback
   http://localhost:8000/api/auth/instagram/callback/
   https://yourdomain.com/auth/instagram/callback
   ```

3. Click **"Save Changes"**

### 3.2 Configure Instagram Settings

1. Go to **Products > Instagram > Basic Display**
2. Add **Valid OAuth Redirect URIs** (same as above)
3. Add **Deauthorize Callback URL**:
   ```
   http://localhost:8000/api/auth/instagram/deauthorize/
   ```
4. Add **Data Deletion Request URL**:
   ```
   http://localhost:8000/api/auth/instagram/data-deletion/
   ```

---

## 🔐 Step 4: Configure Permissions

### 4.1 App Review (For Production)

For development, you can test without app review. For production:

1. Go to **App Review > Permissions and Features**
2. Request these permissions:
   - `instagram_basic` - Access to profile
   - `instagram_manage_messages` - Send/receive DMs
   - `instagram_manage_comments` - Reply to comments
   - `pages_show_list` - List Facebook pages
   - `pages_read_engagement` - Read page data

3. Fill in **Use Case** explanations
4. Submit for review (takes 1-3 days)

### 4.2 Test Users (For Development)

1. Go to **Roles > Test Users**
2. Add test Instagram accounts
3. These can use your app immediately without review

---

## 💻 Step 5: Backend Setup

### 5.1 Install Backend Files

Copy `BACKEND_OAUTH_ENDPOINTS.py` content to your `accounts/views.py`:

```bash
# The file contains:
# - instagram_oauth_initiate()
# - instagram_oauth_callback()
# - disconnect_instagram_account()
# - refresh_instagram_stats()
```

### 5.2 Update URLs

Add to `accounts/urls.py`:

```python
from .views import (
    instagram_oauth_initiate,
    instagram_oauth_callback,
    disconnect_instagram_account,
    refresh_instagram_stats
)

urlpatterns = [
    # OAuth
    path('auth/instagram/oauth/', instagram_oauth_initiate, name='instagram_oauth'),
    path('auth/instagram/callback/', instagram_oauth_callback, name='instagram_callback'),
    
    # Instagram accounts
    path('instagram-accounts/<uuid:account_id>/disconnect/', disconnect_instagram_account),
    path('instagram-accounts/<uuid:account_id>/refresh_stats/', refresh_instagram_stats),
]
```

### 5.3 Update Settings

Add to `core/settings.py`:

```python
# Instagram OAuth
FACEBOOK_APP_ID = config('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = config('FACEBOOK_APP_SECRET')
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    FRONTEND_URL,
]
```

### 5.4 Install Required Package

```bash
pip install requests
```

---

## 🎨 Step 6: Frontend Setup

### 6.1 Install Frontend Files

Copy `COMPLETE_SETTINGS_WITH_OAUTH.tsx` to:
```
src/components/Layout/SettingsPopup.tsx
```

### 6.2 Update API Client

Add to `src/utils/api.ts`:

```typescript
async disconnectInstagramAccount(id: string) {
  await this.client.delete(`/instagram-accounts/${id}/disconnect/`);
}
```

### 6.3 Add to Main App

Make sure SettingsPopup is imported in your layout:

```typescript
import { SettingsPopup } from '../components/Layout/SettingsPopup';

// In your layout component
<SettingsPopup />
```

---

## 🧪 Step 7: Testing

### 7.1 Test OAuth Flow

1. **Start Backend:**
   ```bash
   python manage.py runserver
   ```

2. **Start Frontend:**
   ```bash
   npm run dev
   ```

3. **Test Connection:**
   - Login to your app
   - Go to Settings > Instagram tab
   - Click "Connect Account"
   - OAuth popup should open
   - Grant permissions
   - Should redirect back with success

### 7.2 Verify Database

Check if Instagram account was saved:

```bash
python manage.py shell

from accounts.models import InstagramAccount
accounts = InstagramAccount.objects.all()
for account in accounts:
    print(f"@{account.username} - Active: {account.is_active}")
```

### 7.3 Test Token

Test if token works:

```python
import requests

account = InstagramAccount.objects.first()
url = f"https://graph.facebook.com/v21.0/{account.instagram_user_id}"
params = {
    'access_token': account.access_token,
    'fields': 'username,followers_count'
}
response = requests.get(url, params=params)
print(response.json())
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: "App Not Set Up"
**Solution:** Make sure Instagram product is added to your app

### Issue 2: "Invalid OAuth Redirect URI"
**Solution:** Check redirect URI matches exactly in Meta Developer settings

### Issue 3: "No Instagram Business Account Found"
**Solution:** 
- Make sure Instagram is Business/Creator account
- Verify it's connected to Facebook Page
- Check Page is published

### Issue 4: "Access Token Invalid"
**Solution:**
- Token may have expired (60 days)
- Implement token refresh logic
- User needs to reconnect

### Issue 5: "Permissions Error"
**Solution:**
- Request app review for production
- Use test users for development
- Check all required permissions are granted

---

## 🔄 Token Refresh (Optional but Recommended)

### Add Token Refresh Endpoint

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_instagram_token(request, account_id):
    """Refresh access token before it expires"""
    try:
        account = InstagramAccount.objects.get(
            id=account_id,
            user=request.user
        )
        
        # Check if token expires soon (within 7 days)
        if account.token_expires_at - timezone.now() > timedelta(days=7):
            return Response({'message': 'Token still valid'})
        
        # Exchange for new long-lived token
        new_token = exchange_for_long_lived_token(account.access_token)
        
        if new_token:
            account.access_token = new_token
            account.token_expires_at = timezone.now() + timedelta(days=60)
            account.save()
            
            return Response({'message': 'Token refreshed successfully'})
        else:
            return Response({'error': 'Failed to refresh token'}, status=500)
            
    except InstagramAccount.DoesNotExist:
        return Response({'error': 'Account not found'}, status=404)
```

### Add Celery Task for Auto-Refresh

```python
from celery import shared_task

@shared_task
def refresh_expiring_tokens():
    """Run daily to refresh tokens expiring within 7 days"""
    expiring_soon = InstagramAccount.objects.filter(
        is_active=True,
        token_expires_at__lte=timezone.now() + timedelta(days=7)
    )
    
    for account in expiring_soon:
        try:
            new_token = exchange_for_long_lived_token(account.access_token)
            if new_token:
                account.access_token = new_token
                account.token_expires_at = timezone.now() + timedelta(days=60)
                account.save()
                logger.info(f"Refreshed token for @{account.username}")
        except Exception as e:
            logger.error(f"Failed to refresh token for @{account.username}: {e}")
```

---

## 📊 Production Checklist

Before going live:

- [ ] App approved by Meta (all permissions)
- [ ] Valid OAuth redirect URIs configured (HTTPS)
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Data deletion callback implemented
- [ ] Token refresh logic implemented
- [ ] Error handling for all API calls
- [ ] Rate limiting implemented
- [ ] Logging configured
- [ ] SSL certificate installed
- [ ] Domain configured in Meta app settings

---

## 🎉 Success!

Your Instagram OAuth is now set up! Users can:
1. Connect their Instagram Business/Creator accounts
2. Grant permissions for DMs and comments
3. Start creating automations
4. Send automated DMs and comment replies

---

## 📚 Additional Resources

- **Meta for Developers:** https://developers.facebook.com/
- **Instagram API Docs:** https://developers.facebook.com/docs/instagram-api
- **Instagram Messaging API:** https://developers.facebook.com/docs/messenger-platform/instagram
- **Graph API Explorer:** https://developers.facebook.com/tools/explorer/

---

## 🆘 Need Help?

If you encounter issues:
1. Check Meta Developer logs
2. Review Django logs
3. Check browser console for frontend errors
4. Verify all redirect URIs match
5. Ensure Instagram account is Business/Creator and linked to Page

---

**Everything is ready to go! 🚀**
