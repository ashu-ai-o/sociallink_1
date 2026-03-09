# SocialLink — System Architecture & Pipeline

**What it is:** An Instagram automation platform. Users connect their Instagram account, create automations that watch for comments or DMs, and the system automatically replies to comments and sends DMs — all in real time.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Tech Stack](#2-tech-stack)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Django App Structure](#4-django-app-structure)
5. [Database Models & Relationships](#5-database-models--relationships)
6. [Full Event Pipeline: Comment → DM Sent](#6-full-event-pipeline-comment--dm-sent)
7. [Celery Task System](#7-celery-task-system)
8. [Rate Limiting & Queue System](#8-rate-limiting--queue-system)
9. [Instagram Service Layer](#9-instagram-service-layer)
10. [WebSocket Real-Time Layer](#10-websocket-real-time-layer)
11. [Authentication Flow](#11-authentication-flow)
12. [Frontend Architecture](#12-frontend-architecture)
13. [API Routing Map](#13-api-routing-map)
14. [Configuration & Environment](#14-configuration--environment)
15. [Error Handling & Retry Logic](#15-error-handling--retry-logic)
16. [Logging Reference](#16-logging-reference)

---

## 1. System Overview

SocialLink watches Instagram for comments and DMs, matches them against user-defined automation rules, then:

1. **Publicly replies** to the comment (optional)
2. **Sends a private DM** to the commenter — optionally AI-enhanced
3. **Tracks everything** — contacts database, trigger history, stats

```
User comments on Instagram post
         │
         ▼
Instagram sends webhook → SocialLink backend
         │
         ├─ Match automation rules
         ├─ Reply to comment publicly  (optional)
         ├─ Send DM to commenter
         └─ Notify dashboard via WebSocket
```

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 6.0 (Python 3.11) |
| **ASGI Server** | Daphne (Django Channels) |
| **API** | Django REST Framework + SimpleJWT |
| **WebSockets** | Django Channels 4 + channels-redis |
| **Task Queue** | Celery 5.6 |
| **Scheduler** | Celery Beat |
| **Message Broker** | Redis 7 |
| **Cache** | Redis (separate DB index) |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **HTTP Client** | httpx (async) |
| **Frontend** | React + Vite + Redux Toolkit |
| **AI Enhancement** | OpenRouter API (Claude 3.5 Sonnet / Haiku fallback) |
| **Instagram API** | Meta Graph API v25.0 |

---

## 3. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
│                                                                  │
│   User's Browser          Instagram Platform                     │
│        │                        │                                │
│        │  HTTPS                 │  Webhook POST                  │
└────────┼────────────────────────┼─────────────────────────────── ┘
         │                        │
         ▼                        ▼
┌────────────────────────────────────────────────────────────────┐
│                        NGINX (prod) / Daphne (dev)             │
│                        port 80/443 → 8000                      │
└──────────────────────────────┬─────────────────────────────────┘
                               │
              ┌────────────────┴──────────────────┐
              │                                   │
              ▼                                   ▼
   ┌────────────────────┐             ┌────────────────────┐
   │  HTTP Requests     │             │  WebSocket (ws://) │
   │  /api/*            │             │  /ws/automations/  │
   │  /api/webhooks/    │             │  /ws/dashboard/    │
   │  /admin/           │             │                    │
   └────────┬───────────┘             └────────┬───────────┘
            │                                  │
            ▼                                  ▼
   ┌────────────────────┐             ┌────────────────────┐
   │  Django Views /    │             │  Django Channels   │
   │  DRF Viewsets      │             │  Consumers         │
   └────────┬───────────┘             └────────┬───────────┘
            │                                  │
            ▼                                  ▼
   ┌──────────────────────────────────────────────────────┐
   │                   Django ORM / Models                │
   │          Automation, Trigger, Contact, User          │
   └──────────────────────┬───────────────────────────────┘
                          │
            ┌─────────────┴──────────────┐
            │                            │
            ▼                            ▼
   ┌──────────────────┐        ┌──────────────────────┐
   │   PostgreSQL /   │        │       Redis           │
   │   SQLite DB      │        │  ┌─ DB 0: Celery      │
   │                  │        │  ├─ DB 0: Channels    │
   │                  │        │  └─ DB 1: Cache       │
   └──────────────────┘        └──────────┬───────────┘
                                          │
                               ┌──────────┴───────────┐
                               │                      │
                               ▼                      ▼
                    ┌──────────────────┐   ┌──────────────────┐
                    │  Celery Worker   │   │  Celery Beat     │
                    │  (async tasks)   │   │  (scheduler)     │
                    └────────┬─────────┘   └──────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Instagram API   │
                    │  graph.instagram │
                    │  .com / v25.0    │
                    └──────────────────┘
```

---

## 4. Django App Structure

```
sociallink_1/
│
├── core/                        ← Project config
│   ├── settings.py              ← All config (Redis, Celery, JWT, CORS, rate limits)
│   ├── urls.py                  ← Root URL router
│   ├── asgi.py                  ← ASGI app (HTTP + WebSocket protocol router)
│   ├── celery.py                ← Celery app init
│   └── middleware.py            ← Rate limiting middleware
│
├── automations/                 ← Core business logic
│   ├── models.py                ← Automation, AutomationTrigger, Contact, AutomationVariant
│   ├── views.py                 ← DRF viewsets (Automation, Trigger, Contact, AI, Analytics)
│   ├── webhooks.py              ← Webhook ingestion + event routing
│   ├── tasks.py                 ← Celery tasks (process, retry, queue, token refresh)
│   ├── consumers.py             ← WebSocket consumers (AutomationConsumer, DashboardConsumer)
│   ├── routing.py               ← WebSocket URL patterns
│   ├── urls.py                  ← REST API URL patterns
│   └── services/
│       └── instagram_service_async.py  ← Instagram API client (send_dm, reply_to_comment, get_comments)
│
├── accounts/                    ← User & Instagram account management
│   ├── models.py                ← User, InstagramAccount, Sessions, Tokens
│   ├── views.py                 ← Auth viewsets (register, login, OAuth, 2FA, sessions)
│   └── urls.py                  ← Auth URL patterns
│
├── analytics/                   ← Usage tracking
│   └── models.py                ← PageVisit, UserEvent, CookieConsent, EnterpriseContact, Feedback
│
└── frontend/                    ← React + Vite app
    ├── src/
    │   ├── pages/               ← Dashboard, Automations, Contacts, Analytics, Settings, Auth
    │   ├── components/          ← Layout, AutomationList, RealTimeDashboard, Forms
    │   ├── store/               ← Redux slices (automations, auth, theme, ui)
    │   └── lib/api.ts           ← Axios API client with JWT auto-refresh
    └── dist/                    ← Built output served by Nginx
```

---

## 5. Database Models & Relationships

```
User (CustomUser)
│   email (unique), google_id, github_id
│   2FA, session tracking, onboarding, preferences
│
└──▶ InstagramAccount (many per user)
     │   instagram_user_id, platform_id, page_id
     │   access_token, token_expires_at
     │   connection_method: 'facebook_graph' | 'instagram_platform'
     │   is_active, username, followers_count
     │
     ├──▶ Automation (many per account)
     │    │   name, trigger_type, trigger_keywords, trigger_match_type
     │    │   target_posts (list of post IDs, empty = all posts)
     │    │   DmMessage, dm_buttons (quick reply buttons)
     │    │   enable_comment_reply, comment_reply_message
     │    │   use_ai_enhancement, ai_context
     │    │   max_triggers_per_user, cooldown_minutes
     │    │   is_active, priority
     │    │   total_triggers, total_dms_sent, total_comment_replies
     │    │
     │    ├──▶ AutomationTrigger (one per event)
     │    │        instagram_user_id, instagram_username
     │    │        post_id, comment_id, comment_text
     │    │        status: pending → processing → sent | failed | skipped | queued
     │    │        error_message, failure_reason
     │    │        comment_reply_sent, comment_reply_text
     │    │        DmMessage_sent, was_ai_enhanced
     │    │        dm_sent_at, comment_reply_sent_at
     │    │
     │    └──▶ AutomationVariant (A/B test variants)
     │             name, DmMessage, traffic_percentage
     │             total_sends, total_clicks, total_conversions
     │
     └──▶ Contact (one per unique Instagram user who received a DM)
              instagram_user_id, instagram_username, full_name
              total_interactions, total_dms_received
              first_interaction, last_interaction
              tags, custom_fields
              is_follower, is_blocked
```

**Trigger Status Flow:**

```
pending ──▶ processing ──▶ sent
   │                  └──▶ failed
   │
   └──▶ queued (rate limited) ──▶ processing ──▶ sent
                                             └──▶ failed
```

---

## 6. Full Event Pipeline: Comment → DM Sent

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Instagram fires webhook                                        │
│                                                                         │
│  POST /api/webhooks/instagram/                                          │
│  Header: X-Hub-Signature-256: sha256=<hmac>                            │
│  Body: { "object": "instagram", "entry": [...] }                       │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Signature verification (webhooks.py → verify_signature())      │
│                                                                         │
│  HMAC-SHA256 using FACEBOOK_APP_SECRET or INSTAGRAM_CLIENT_SECRET       │
│  DEBUG bypass: signature == "any" skips check (local dev only)          │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Account lookup (webhooks.py → process_entry())                 │
│                                                                         │
│  entry.id is matched against InstagramAccount:                          │
│  1st try → instagram_user_id                                            │
│  2nd try → platform_id                                                  │
│  3rd try → page_id                                                      │
│  Not found? → log warning, skip                                         │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               │ entry.changes[]               │ entry.messaging[]
               ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────────────────┐
│ COMMENT EVENT            │    │ DM / STORY EVENT                     │
│ process_change()         │    │ process_message()                    │
│ handle_comment()         │    │                                      │
│                          │    │ Ignore echo (sender == own account)  │
│ Extract:                 │    │                                      │
│ - media_id (flat/nested) │    │ Route to:                            │
│ - comment_id             │    │ - handle_story_mention()             │
│ - text                   │    │ - handle_story_reply()               │
│ - from.id + from.username│    │ - handle_dm_keyword()                │
│                          │    │                                      │
│ No from.id?              │    │                                      │
│  → use comment:id        │    │                                      │
│    as sentinel user_id   │    │                                      │
└────────────┬─────────────┘    └────────────────────────────────────┘
             │                               │
             └──────────────┬────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 4: Automation matching (webhooks.py → should_trigger_automation())│
│                                                                         │
│  For each active automation with matching trigger_type:                 │
│                                                                         │
│  Check target_posts:                                                    │
│    - Empty list → match ALL posts                                       │
│    - Has entries → post_id must be in list                              │
│                                                                         │
│  Check trigger_match_type:                                              │
│    'any'      → always matches (good for empty text too)               │
│    'exact'    → keyword == comment text (case-insensitive)             │
│    'contains' → keyword in comment text (case-insensitive)             │
│                                                                         │
│  Empty comment text + 'exact'/'contains' → warns, skips               │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ matched
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 5: Create trigger record                                          │
│                                                                         │
│  AutomationTrigger.objects.create(                                      │
│      automation=automation,                                             │
│      instagram_user_id=user_id,       # or 'comment:<id>' sentinel     │
│      instagram_username=username,                                       │
│      post_id=media_id,                                                  │
│      comment_id=comment_id,                                             │
│      comment_text=comment_text,                                         │
│      status='pending'                                                   │
│  )                                                                      │
│  automation.total_triggers += 1                                         │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 6: Dispatch to Celery                                             │
│                                                                         │
│  process_automation_trigger_async.delay(trigger.id)                    │
│  Webhook returns 200 OK immediately (Celery failure doesn't crash it)  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
    ┌──────────────────────────┘  (async, in Celery worker process)
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 7: Rate limit checks (tasks.py → _process_trigger_with_rate_limit)│
│                                                                         │
│  A) 24-hour per-user rule                                               │
│     cache.get(f'dm_user:{account_id}:{user_id}')                       │
│     Already sent → status='skipped', stop                              │
│                                                                         │
│  B) 200 DMs/hour account limit                                          │
│     cache.get(f'dm_count:{account_id}:{hour_key}')                     │
│     Limit reached → status='queued', WebSocket notify, stop            │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ passed
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 8: Public comment reply (optional)                                │
│                                                                         │
│  if automation.enable_comment_reply and trigger.comment_id:            │
│      POST /{comment_id}/replies                                         │
│      {"message": comment_reply_message}                                 │
│                                                                         │
│  trigger.comment_reply_sent = True                                      │
│  trigger.comment_reply_text = reply_message                             │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 9: AI message enhancement (optional)                              │
│                                                                         │
│  if automation.use_ai_enhancement:                                      │
│      AIServiceOpenRouter.enhance_message(                               │
│          original_message=automation.DmMessage,                         │
│          comment_text=trigger.comment_text,                             │
│          ai_context=automation.ai_context,                              │
│          username=trigger.instagram_username                             │
│      )                                                                  │
│      Primary model:  Claude 3.5 Sonnet (via OpenRouter)                │
│      Fallback model: Claude 3 Haiku                                     │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 10: Send DM (instagram_service_async.py → send_dm())             │
│                                                                         │
│  POST /me/messages  (graph.instagram.com or graph.facebook.com)        │
│                                                                         │
│  Recipient resolution:                                                  │
│    comment_id provided    → {"comment_id": comment_id}                 │
│    user_id = 'comment:X'  → {"comment_id": X}  (no from.id case)      │
│    normal user_id         → {"id": user_id}                            │
│                                                                         │
│  Payload:                                                               │
│    {"recipient": {...}, "message": {"text": "...", "quick_replies": []}}│
└──────────────────────────────┬───────────────────┬──────────────────────┘
                               │ success           │ failure
                               ▼                   ▼
┌──────────────────────┐  ┌─────────────────────────────────────────────┐
│  SUCCESS             │  │  FAILURE                                    │
│                      │  │                                             │
│  rate_limit++        │  │  Permanent error subcodes (no retry):       │
│  mark_user_sent()    │  │    2534014 → user not found / dev mode      │
│  trigger.status=sent │  │    2018034 → user disabled messages         │
│  trigger.dm_sent_at  │  │    2018001 → app not authorized             │
│  Contact.upsert()    │  │    551     → cannot receive messages        │
│  automation.total    │  │                                             │
│  _dms_sent++         │  │  Transient errors:                          │
│  automation.total    │  │    retry up to 3x, countdown = 2^retries   │
│  _comment_replies++  │  │    (2s → 4s → 8s)                           │
│                      │  │                                             │
│  WebSocket:          │  │  trigger.status = 'failed'                  │
│  dm_sent event       │  │  trigger.error_message = ...                │
└──────────────────────┘  └─────────────────────────────────────────────┘
```

---

## 7. Celery Task System

### Scheduled Tasks (Celery Beat)

```
Every 30s  ─── retry_pending_triggers()
               Safety net: re-dispatches 'pending' triggers < 24h old
               Logs heartbeat with counts: pending/processing/sent/failed

Every 1h   ─── process_queued_triggers()   [at :00 each hour]
               Processes 'queued' triggers within remaining hourly quota
               Oldest-first per account

Every 24h  ─── refresh_instagram_tokens()
               Refreshes instagram_platform tokens expiring within 15 days
               GET /refresh_access_token?grant_type=ig_refresh_token
```

### Main Processing Task

```
process_automation_trigger_async(trigger_id)
│
│  Config: max_retries=3, time_limit=300s, bind=True (self access)
│
├── Load trigger + automation + instagram_account from DB
├── Rate limit checks (cache-based)
│   ├── 24h per-user  → skip
│   └── 200/h account → queue + WebSocket notify
│
├── [async] reply_to_comment()  ← POST /{comment_id}/replies
├── [async] enhance_message()   ← OpenRouter API (optional)
├── [async] send_dm()           ← POST /me/messages
│
├── On success:
│   ├── Increment cache counters
│   ├── Update trigger record (sent, dm_sent_at, DmMessage_sent)
│   ├── Upsert Contact record
│   ├── Update Automation stats
│   └── WebSocket broadcast: dm_sent event
│
└── On failure:
    ├── Permanent error → mark failed, no retry
    └── Transient error → self.retry(countdown=2^retries)
```

### WebSocket Notifications from Celery

| Event | Triggered When | Data Sent |
|---|---|---|
| `automation_triggered` | Trigger created | automation_id, trigger_data |
| `trigger_queued` | Rate limit hit | queue_size, reset_time |
| `dm_sent` | DM success | automation_id, recipient, status, comment_reply_sent |

---

## 8. Rate Limiting & Queue System

### Instagram API Limits Enforced

```
┌─────────────────────────────────────────────────────┐
│  InstagramRateLimiter (tasks.py)                    │
│                                                     │
│  Per account, per hour:  200 DMs max               │
│  Cache key: dm_count:{account_id}:{YYYY-MM-DD-HH}  │
│  TTL: minutes remaining in current hour             │
│                                                     │
│  Per user, per 24h:      1 DM max                  │
│  Cache key: dm_user:{account_id}:{user_id}         │
│  TTL: 86400s (24 hours)                             │
└─────────────────────────────────────────────────────┘
```

### Queue Flow

```
Rate limit hit
     │
     ▼
trigger.status = 'queued'
trigger.queued_at = now()
WebSocket → trigger_queued event (shows user: "will send at HH:00")
     │
     ▼
Celery Beat: process_queued_triggers() runs at top of each hour
     │
     ▼
For each account:
  remaining_quota = 200 - current_hour_count
  get oldest N queued triggers (up to remaining_quota)
  dispatch each → process_automation_trigger_async.delay()
```

### API Rate Limiting (Django Middleware)

```
Anonymous users: 100 requests/hour
Authenticated users: 1000 requests/hour
Middleware: core.middleware.RateLimitMiddleware
```

---

## 9. Instagram Service Layer

### Connection Methods

| Method | Base URL | Used For |
|---|---|---|
| `instagram_platform` | `graph.instagram.com/v25.0` | New direct Instagram API |
| `facebook_graph` | `graph.facebook.com/v25.0` | Legacy Facebook Page-linked accounts |

### API Calls Made

```
send_dm()
  POST /me/messages
  Recipient: {"comment_id": X} | {"id": user_id}
  Body: text + optional quick_replies buttons

reply_to_comment()
  POST /{comment_id}/replies
  Body: message text

get_comments()
  GET /{post_id}/comments?fields=id,text,username,from,timestamp
  Handles pagination (cursors) automatically

check_if_following()
  GET — verifies if user follows the account before sending DM

refresh_access_token()  [in tasks.py, not service]
  GET /refresh_access_token?grant_type=ig_refresh_token&access_token=X
```

### Token Lifecycle

```
Instagram Platform token lifespan: ~60 days

Daily check (Celery Beat):
  token_expires_at <= now + 15 days → refresh
  Save new token + new token_expires_at to DB
```

---

## 10. WebSocket Real-Time Layer

### Architecture

```
Browser ──ws://─▶ Daphne ──▶ Django Channels ──▶ channels-redis ◀── Celery
                                                  (channel layer)     (publishes events)
```

### WebSocket Endpoints

| URL | Consumer | Purpose |
|---|---|---|
| `/ws/automations/` | `AutomationConsumer` | Live automation list + toggle |
| `/ws/automations/{id}/` | `AutomationConsumer` | Single automation events |
| `/ws/dashboard/` | `DashboardConsumer` | Stats refresh every 5s |

### Channel Groups

```
user_{user_id}          ← per-user group, all automations for that user
dashboard_{user_id}     ← dashboard stats stream
```

### AutomationConsumer — Message Types

**From client → server:**

| Action | What Happens |
|---|---|
| `get_automations` | Returns full automation list for the user |
| `toggle_automation` | Flips is_active in DB, broadcasts to group |
| `subscribe_automation` | Joins automation-specific sub-group |

**From server → client (pushed by Celery):**

| Event | When | Payload |
|---|---|---|
| `automation_updated` | Toggle | `{automation_id, is_active}` |
| `automation_triggered` | Trigger created | `{automation_id, trigger_data}` |
| `trigger_queued` | Rate limit | `{trigger_data, queue_position, reset_time}` |
| `dm_sent` | DM sent/failed | `{automation_id, recipient, status, comment_reply_sent}` |

### DashboardConsumer

- Pushes `stats_update` every 5 seconds
- Stats: `total_automations`, `active_automations`, `total_dms_sent`, `total_triggers`, `today_triggers`

---

## 11. Authentication Flow

### Standard Login

```
1. POST /api/auth/token/
   Body: {email, password}
   Response: {access: "...", refresh: "..."}

2. All subsequent requests:
   Header: Authorization: Bearer <access_token>

3. Token expires after 1h:
   POST /api/auth/token/refresh/
   Body: {refresh: "..."}
   Response: {access: "new_token", refresh: "rotated_refresh"}
   → Old refresh token is blacklisted (rotation enabled)
```

### Instagram OAuth Connection

```
1. GET /api/auth/instagram/oauth/
   → Returns OAuth URL (Meta App login page)

2. User authorizes on Instagram
   → Meta redirects to callback URL with ?code=...

3. Backend exchanges code for access_token
   → Creates / updates InstagramAccount record
   → Stores: instagram_user_id, platform_id, access_token, token_expires_at
```

### Optional 2FA

```
Enable: POST /api/auth/2fa/enable/   → returns QR code + backup codes
Verify: POST /api/auth/2fa/verify/   → requires TOTP code on each login
Backup: POST /api/auth/2fa/backup/   → use backup code if authenticator lost
```

### JWT Config

| Setting | Value |
|---|---|
| Access token lifetime | 1 hour |
| Refresh token lifetime | 7 days |
| Rotation | Enabled (new refresh on each use) |
| Blacklist after rotate | Enabled |
| Algorithm | HS256 |

---

## 12. Frontend Architecture

### Page Structure

```
/                 → Landing page
/login            → Auth: Login
/register         → Auth: Register
/dashboard        → Dashboard (WebSocket real-time stats)
/automations      → Automation list + create/edit (WebSocket updates)
/contacts         → Lead/contact database (searchable, exportable)
/analytics        → Performance metrics (charts, date range)
/settings         → Account settings, Instagram connect, 2FA, sessions
/pricing          → Pricing page
```

### Redux Store

```
store/
├── automationsSlice
│   ├── State: items[], currentAutomation, loading, error
│   ├── Filters: status, search
│   └── Thunks: fetchAutomations, createAutomation, updateAutomation,
│               deleteAutomation, toggleAutomation
│
├── authSlice
│   ├── State: user, tokens, isAuthenticated, loading
│   └── Thunks: login, register, logout, refreshToken
│
├── themeSlice
│   └── State: mode (light/dark)
│
└── uiSlice
    └── State: sidebarOpen, modals, notifications
```

### API Client (src/lib/api.ts)

```
ApiClient (axios instance)
│
├── Base URL: VITE_API_URL (default: http://localhost:8000/api)
├── Interceptor: Attach Authorization: Bearer <token> to every request
└── Interceptor: On 401 → auto-refresh token → retry original request
                          On refresh failure → logout user
```

### WebSocket Connection (frontend)

```
AutomationsPageRealTime.tsx
  ws://localhost:8000/ws/automations/
  → Listen for: dm_sent, automation_triggered, trigger_queued
  → Dispatch: Redux actions to update live state

RealTimeDashboard.tsx
  ws://localhost:8000/ws/dashboard/
  → Receive: stats_update every 5s → update counters
```

---

## 13. API Routing Map

```
/admin/                                   → Django admin panel

/health/                                  → Health check (GET)

/api/auth/
  POST   token/                           → Get JWT tokens (login)
  POST   token/refresh/                   → Refresh JWT
  POST   register/                        → Create account
  POST   logout/                          → Blacklist refresh token
  GET    instagram/oauth/                 → Get Instagram OAuth URL
  GET/POST  instagram/callback/           → OAuth callback
  POST   2fa/enable/                      → Enable 2FA
  POST   2fa/verify/                      → Verify TOTP code
  GET    sessions/                        → Active sessions
  DELETE sessions/{id}/                   → Revoke session

/api/webhooks/instagram/
  GET                                     → Webhook verification (hub.challenge)
  POST                                    → Receive Instagram events

/api/automations/
  GET/POST                                → List / Create automations
  GET/PUT/DELETE  {id}/                   → Retrieve / Update / Delete
  POST   {id}/toggle/                     → Activate / Deactivate
  POST   {id}/test_trigger/              → Simulate a test trigger
  POST   {id}/test_ai_enhancement/       → Preview AI message
  GET    {id}/analytics/                  → Per-automation stats
  POST   {id}/duplicate/                  → Clone automation

/api/triggers/
  GET                                     → List all triggers (filterable)
  GET    {id}/                            → Trigger detail
  GET    export/                          → Download CSV/Excel

/api/contacts/
  GET                                     → Contact list (searchable)
  GET    {id}/                            → Contact detail
  GET    search/                          → Full-text search
  GET    export/                          → Download CSV/Excel

/api/instagram-accounts/
  GET/POST                                → List / Connect account
  DELETE {id}/                            → Remove account
  POST   {id}/disconnect/                 → Disconnect (keep record)
  POST   {id}/refresh_stats/             → Sync followers/media count

/api/analytics/
  GET    dashboard/                       → Overall stats
  GET    automations/                     → Per-automation breakdown
  GET    export_analytics/               → Export report

/api/ai-providers/
  GET    status/                          → Which AI providers are active
  POST   test/                            → Send test prompt

ws/automations/                           → WebSocket: live automation events
ws/automations/{id}/                      → WebSocket: single automation events
ws/dashboard/                             → WebSocket: dashboard stats
```

---

## 14. Configuration & Environment

### Required Environment Variables

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (default: SQLite)
DATABASE_URL=postgresql://user:pass@localhost:5432/sociallink_db

# Redis
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_HOST=127.0.0.1

# Instagram / Meta
INSTAGRAM_WEBHOOK_VERIFY_TOKEN=your_verify_token
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
INSTAGRAM_CLIENT_SECRET=your_ig_secret

# AI
ANTHROPIC_API_KEY=your_key        # for OpenRouter
OPENROUTER_API_KEY=your_key

# App URLs
BACKEND_URL=https://yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

### Redis Key Map

```
dm_count:{account_id}:{YYYY-MM-DD-HH}    → hourly DM counter (TTL: end of hour)
dm_user:{account_id}:{user_id}           → 24h send lock (TTL: 86400s)
```

### Celery Beat Schedule

| Task | Interval | Purpose |
|---|---|---|
| `retry_pending_triggers` | Every 30s | Safety net for stuck pending triggers |
| `process_queued_triggers` | Every hour at :00 | Drain queue when rate limit resets |
| `refresh_instagram_tokens` | Every 24h | Keep tokens alive (refresh if < 15 days left) |

---

## 15. Error Handling & Retry Logic

### DM Permanent Errors (Never Retry)

| Subcode | Meaning | Cause |
|---|---|---|
| `2534014` | User not found / not reachable | Dev mode — user not a Test User |
| `2018034` | User disabled message receiving | User turned off message requests |
| `2018001` | App not authorized by user | User hasn't authorized the app |
| `551` | Cannot receive messages | Account restricted |

### Transient Errors (Retry with Backoff)

```
Attempt 1 fails → wait 2s  → retry
Attempt 2 fails → wait 4s  → retry
Attempt 3 fails → wait 8s  → mark failed, no more retries
```

### Webhook Resilience

```
Celery down when webhook arrives?
  → Trigger saved as 'pending' in DB
  → retry_pending_triggers() picks it up within 30 seconds

Celery task crashes mid-flight?
  → retry_pending_triggers() re-dispatches after 30s
  → Won't duplicate: status check prevents re-processing 'sent' triggers

Instagram doesn't receive 200 in time?
  → Webhook returns 200 immediately (before Celery task runs)
  → Instagram won't retry the webhook
```

---

## 16. Logging Reference

All logs use structured prefixes for easy `grep` in production:

```
[WEBHOOK]             Incoming webhook received
[COMMENT]             Comment parsed from webhook
[FILTER]              Automation matching decision (MATCHED / SKIPPED)
[TRIGGER]             Trigger record created / dispatched
[DM]                  DM send attempt
[send_dm]             DM API response (success / error details)
[BEAT]                Celery Beat heartbeat (every 30s)
[retry_pending]       Pending trigger retry sweep
[token_refresh]       Token refresh operation
[PROCESS]             Celery task processing
[POLL]                Comment polling (fallback mode)
[get_comments]        Comment fetch from Instagram API
[DEV]                 Development-only skip/bypass messages
[WARNING]             Non-fatal issues (empty text, missing from.id, etc.)
[ERROR]               Fatal errors requiring attention
```

**Quick debug commands:**
```bash
# Watch all DM activity
journalctl -u sociallink-celery -f | grep "\[DM\]\|\[send_dm\]"

# Watch webhook ingestion
journalctl -u sociallink-daphne -f | grep "\[WEBHOOK\]\|\[COMMENT\]\|\[TRIGGER\]"

# Watch automation matching
journalctl -u sociallink-celery -f | grep "\[FILTER\]"

# Watch rate limiter
journalctl -u sociallink-celery -f | grep "Rate limit\|queued\|quota"
```
