# Testing Comment & DM Triggers via Graph API Explorer

This guide shows you how to use [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/) to verify your posts have comments, simulate comment events, and end-to-end test the entire comment → DM automation pipeline.

---

## 1. Get Your Access Token

Open [Graph API Explorer](https://developers.facebook.com/tools/explorer/):

1. Select your **App** (top-right dropdown)
2. Click **Generate Access Token**
3. Grant these permissions:
   - `instagram_basic`
   - `instagram_manage_comments`
   - `instagram_manage_messages`
   - `pages_read_engagement` *(facebook_graph accounts only)*

> **Tip:** The generated token is short-lived (~1h). For repeated testing paste your long-lived account token from the Django admin instead.

---

## 2. Find Your Instagram User ID

### instagram_platform accounts
```
GET https://graph.instagram.com/v25.0/me?fields=id,username&access_token=YOUR_TOKEN
```

### facebook_graph accounts
```
GET https://graph.facebook.com/v25.0/me/accounts?fields=id,name,instagram_business_account&access_token=YOUR_TOKEN
```
The `instagram_business_account.id` is your Instagram user ID.

---

## 3. List Your Posts / Reels

Replace `YOUR_IG_USER_ID` with the ID from step 2.

### instagram_platform
```
GET https://graph.instagram.com/v25.0/YOUR_IG_USER_ID/media
    ?fields=id,caption,media_type,timestamp,permalink
    &access_token=YOUR_TOKEN
```

### facebook_graph
```
GET https://graph.facebook.com/v25.0/YOUR_IG_USER_ID/media
    ?fields=id,caption,media_type,timestamp,permalink
    &access_token=YOUR_TOKEN
```

**Response example:**
```json
{
  "data": [
    {
      "id": "17854360229135492",
      "caption": "Check this out!",
      "media_type": "REEL",
      "timestamp": "2026-03-07T12:00:00+0000",
      "permalink": "https://www.instagram.com/reel/ABC123/"
    }
  ]
}
```

Copy the `id` — this is your **`media_id` / `post_id`** used in automations.

---

## 4. Fetch Comments on a Post

Replace `MEDIA_ID` with any id from step 3.

### instagram_platform
```
GET https://graph.instagram.com/v25.0/MEDIA_ID/comments
    ?fields=id,text,username,from,timestamp
    &access_token=YOUR_TOKEN
```

### facebook_graph
```
GET https://graph.facebook.com/v25.0/MEDIA_ID/comments
    ?fields=id,text,username,from,timestamp
    &access_token=YOUR_TOKEN
```

**Response example:**
```json
{
  "data": [
    {
      "id": "17858893269135681",
      "text": "send me the link!",
      "username": "john_doe",
      "from": { "id": "123456789", "name": "John Doe" },
      "timestamp": "2026-03-08T09:00:00+0000"
    }
  ]
}
```

> **If `data` is empty:** Nobody has commented yet. Either post a real comment from a test account, or use the webhook simulation in step 6.

---

## 5. Verify Your Automation is Configured Correctly

Before sending any test webhook, make sure the automation matches:

| Automation Setting | What to Check |
|---|---|
| `trigger_type` | Must be `comment` |
| `trigger_match_type` | `any` fires on every comment; `contains`/`exact` require matching keywords |
| `trigger_keywords` | Must match words in your test comment (case-insensitive) |
| `target_posts` | Either empty (match all posts) or must include your `MEDIA_ID` |
| `is_active` | Must be `True` |
| `dm_message` | The DM text sent to the commenter |

Check in Django admin: `/admin/automations/automation/`

---

## 6. Simulate a Comment Webhook (Test End-to-End)

This sends a fake webhook payload to your local server — exactly what Instagram would send when someone comments.

### A. Start your server + ngrok + Celery
```bash
# Terminal 1
python manage.py runserver

# Terminal 2
celery -A core worker --loglevel=info

# Terminal 3 (if not running)
ngrok http 8000
```

### B. Send the test webhook with curl

Replace values marked with `YOUR_*`:

```bash
curl -X POST http://localhost:8000/api/webhooks/instagram/ \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=any" \
  -d '{
    "object": "instagram",
    "entry": [
      {
        "id": "YOUR_IG_ACCOUNT_ID",
        "time": 1741420800,
        "changes": [
          {
            "field": "comments",
            "value": {
              "media": {
                "id": "YOUR_MEDIA_ID",
                "media_product_type": "REEL"
              },
              "id": "FAKE_COMMENT_ID_001",
              "text": "send me the link",
              "from": {
                "id": "TEST_USER_IG_ID",
                "username": "test_commenter"
              }
            }
          }
        ]
      }
    ]
  }'
```

> `X-Hub-Signature-256: sha256=any` works in **DEBUG=True** mode — the signature check is bypassed.

**Expected webhook response:**
```json
{"status": "success"}
```

### C. Watch the Celery worker logs

You should see a sequence like:
```
[COMMENT] New comment on media_id=YOUR_MEDIA_ID | comment_id=FAKE_COMMENT_ID_001 | from @test_commenter | text="send me the link"
[FILTER] Automation "My Automation" MATCHED (contains) on "send me the link"
[TRIGGER] ✓ Created trigger 42 for automation "My Automation"
[TRIGGER] Task queued for trigger 42
[PROCESS] Processing trigger 42 ...
[DM] Sending DM to user TEST_USER_IG_ID ...
```

---

## 7. Test the `from.id` Missing Scenario

Instagram Platform API sometimes omits `from.id` for users who haven't authorized your app.
The code handles this by using `comment_id` as the DM recipient instead.

```bash
curl -X POST http://localhost:8000/api/webhooks/instagram/ \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=any" \
  -d '{
    "object": "instagram",
    "entry": [
      {
        "id": "YOUR_IG_ACCOUNT_ID",
        "time": 1741420800,
        "changes": [
          {
            "field": "comments",
            "value": {
              "media": { "id": "YOUR_MEDIA_ID" },
              "id": "REAL_COMMENT_ID_FROM_STEP_4",
              "text": "send me the link",
              "from": {}
            }
          }
        ]
      }
    ]
  }'
```

Expected log:
```
[COMMENT] comment_id=REAL_COMMENT_ID_FROM_STEP_4 has no user id in "from" field ...
Will attempt DM via comment_id recipient instead of user_id.
```

The DM call will use `{"comment_id": "REAL_COMMENT_ID_FROM_STEP_4"}` as the recipient — which is a valid Instagram Messaging API recipient format.

---

## 8. Test a Real Comment → DM Flow (Production-Like)

1. Add a **Test User** in Meta App Dashboard → Roles → Test Users
2. Have the test user comment on your post (use a real device or the Instagram app)
3. Watch Django + Celery logs — the webhook fires automatically if ngrok is running and subscribed
4. Confirm the test user received the DM

---

## 9. Common Issues & Fixes

| Symptom | Cause | Fix |
|---|---|---|
| `data: []` on comments fetch | No comments yet | Post a real comment from another account |
| Webhook returns `403 Invalid signature` | `DEBUG=False` or wrong signature | Set `DEBUG=True` or send real HMAC |
| `No active comment automations found` | Automation inactive or wrong account | Check automation `is_active` and `instagram_account` in admin |
| DM fails with subcode `2534014` | User in dev mode hasn't authorized app | Add them as a Test User in Meta App Dashboard |
| DM fails with subcode `2018034` | Trying to DM yourself (echo) | Use a different test user ID |
| `Automation SKIPPED - no exact match` | Comment text doesn't match keyword | Change `trigger_match_type` to `any` for testing |
| Empty `text` in comment | Meta Dev Console test button | Use a real comment or the curl simulation above |
| `target_posts` mismatch | Post ID not in automation's target list | Clear `target_posts` or add the media_id |

---

## 10. Quick Reference — Key IDs

Run this Django shell snippet to print all the IDs you need:

```bash
python manage.py shell
```

```python
from automations.models import Automation, InstagramAccount

for acc in InstagramAccount.objects.filter(is_active=True):
    print(f"\nAccount: @{acc.username}")
    print(f"  instagram_user_id : {acc.instagram_user_id}")
    print(f"  platform_id       : {acc.platform_id}")
    print(f"  page_id           : {acc.page_id}")
    print(f"  connection_method : {acc.connection_method}")
    for auto in Automation.objects.filter(instagram_account=acc, trigger_type='comment'):
        print(f"  Automation: {auto.name} | active={auto.is_active} | match={auto.trigger_match_type} | keywords={auto.trigger_keywords} | target_posts={auto.target_posts}")
```
