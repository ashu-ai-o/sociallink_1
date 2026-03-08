# Testing & Sharing Your App — Tunnel & Free Hosting Options

For when you need a **public HTTPS URL** to test Instagram webhooks, share with teammates,
or test on a real phone — without touching production.

Stack: Django 6 (ASGI/Daphne) + React (Vite) + Celery + Redis

---

## Quick Comparison

| Tool | Cost | Speed | Persistent URL | Webhooks | WebSockets | Best For |
|---|---|---|---|---|---|---|
| **ngrok** | Free / $10/mo | Instant | Paid only | ✅ | ✅ | Local webhook testing |
| **Cloudflare Tunnel** | Free | 2 min setup | ✅ | ✅ | ✅ | Best free option |
| **localtunnel** | Free | Instant | ❌ | ✅ | ⚠️ | Quick demos |
| **Railway** | $5 credit free | ~5 min | ✅ | ✅ | ✅ | Full stack testing |
| **Render** | Free tier | ~3 min | ✅ | ✅ | ✅ | Staging environment |
| **Netlify** | Free | ~2 min | ✅ | Frontend only | ❌ | Frontend only |

---

## Method 1: ngrok (Already Set Up in This Project)

> Your settings.py already whitelists `*.ngrok-free.app` and `*.ngrok.io` automatically in DEBUG mode.

### Install
```bash
# Mac
brew install ngrok

# Linux
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc > /dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Or just download from https://ngrok.com/download
```

### Sign up & authenticate (free)
```bash
ngrok config add-authtoken YOUR_TOKEN_FROM_NGROK_DASHBOARD
```

### Run
```bash
# Terminal 1 — Django
python manage.py runserver 8000

# Terminal 2 — Celery
celery -A core worker --loglevel=info

# Terminal 3 — ngrok
ngrok http 8000
```

You'll see:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

### Register the webhook
```bash
python manage.py setup_webhook --url https://abc123.ngrok-free.app
```

### Problems with free ngrok

| Problem | Cause | Fix |
|---|---|---|
| URL changes every restart | Free plan | Pay $10/mo for fixed domain, or use Method 2 |
| Browser shows "ngrok warning page" | Free plan interstitial | Add `ngrok-skip-browser-warning: true` header or pay |
| Tunnel dies after ~2h inactive | Free plan limit | Restart `ngrok http 8000` |

### ngrok Free vs Paid

| Feature | Free | Paid ($10/mo) |
|---|---|---|
| Fixed subdomain | ❌ | ✅ `yourname.ngrok.app` |
| Multiple tunnels | 1 | Unlimited |
| Inspect dashboard | ✅ localhost:4040 | ✅ |
| Custom domain | ❌ | ✅ |

---

## Method 2: Cloudflare Tunnel (Free, Permanent URL)

> Best free option. Persistent URL, no restarts, works with webhooks and WebSockets.

### Install cloudflared
```bash
# Linux
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared

# Mac
brew install cloudflared
```

### One-time setup (needs a free domain on Cloudflare)
```bash
cloudflared tunnel login          # opens browser
cloudflared tunnel create sociallink-dev
```

### Quick tunnel (no domain needed, temporary URL)
```bash
# This gives you a random https URL instantly, no account needed
cloudflared tunnel --url http://localhost:8000
```

### Permanent tunnel with your domain
Create `~/.cloudflared/config.yml`:
```yaml
tunnel: YOUR-TUNNEL-ID
credentials-file: /home/user/.cloudflared/YOUR-TUNNEL-ID.json

ingress:
  - hostname: dev.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

```bash
cloudflared tunnel route dns sociallink-dev dev.yourdomain.com
cloudflared tunnel run sociallink-dev
```

### Add to Django ALLOWED_HOSTS / CORS

In your `.env`:
```env
ALLOWED_HOSTS=localhost,127.0.0.1,dev.yourdomain.com
```

In `core/settings.py`, add to `CORS_ALLOWED_ORIGINS`:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://dev.yourdomain.com",   # add this
]
```

---

## Method 3: localtunnel (Zero Setup, No Account)

> Instant public URL. No signup. Good for 5-minute demos.

```bash
npm install -g localtunnel
```

```bash
# Start your Django server first
python manage.py runserver 8000

# Then tunnel
lt --port 8000 --subdomain mysociallink
# → https://mysociallink.loca.lt
```

### Limitations
- URL is not guaranteed (someone else may have `mysociallink`)
- Occasionally goes down
- WebSockets work but are unreliable
- Not suitable for Instagram webhooks (too unstable)

---

## Method 4: Railway (Free $5 Credit — Full Stack)

> Deploy Django + Celery + Redis + PostgreSQL all together. Real URLs, real HTTPS.

### What Railway gives you free
- $5/month credit (enough for small test deployments)
- PostgreSQL included
- Redis included
- Auto-deploys from GitHub

### Setup

1. Push your repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Add services:
   - **PostgreSQL** (click Add → Database → PostgreSQL)
   - **Redis** (click Add → Database → Redis)

### Environment Variables (Railway Dashboard → Variables)

```env
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}}
DATABASE_URL=${{POSTGRES_URL}}          # auto-set by Railway
REDIS_URL=${{REDIS_URL}}               # auto-set by Railway
REDIS_HOST=${{REDIS_HOST}}
INSTAGRAM_WEBHOOK_VERIFY_TOKEN=your_token
FACEBOOK_APP_ID=your_id
FACEBOOK_APP_SECRET=your_secret
BACKEND_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}
```

### Procfile (create in project root)

```
web: daphne -b 0.0.0.0 -p $PORT core.asgi:application
worker: celery -A core worker --loglevel=info --concurrency=2
beat: celery -A core beat --loglevel=info
release: python manage.py migrate
```

### Build Command (Railway → Settings → Build)

```bash
pip install -r requirements.txt && cd frontend && npm install && npm run build && cd .. && python manage.py collectstatic --noinput
```

### Start Command
```
daphne -b 0.0.0.0 -p $PORT core.asgi:application
```

Railway auto-assigns a public URL like `https://sociallink-production.up.railway.app`

---

## Method 5: Render (Free Tier — Easiest Platform)

> Free tier available, PostgreSQL free for 90 days, Redis free tier.

### Setup

1. Push repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect GitHub repo

### Render Config

`render.yaml` (create in project root):
```yaml
services:
  - type: web
    name: sociallink-backend
    env: python
    buildCommand: |
      pip install -r requirements.txt
      python manage.py collectstatic --noinput
      python manage.py migrate
    startCommand: daphne -b 0.0.0.0 -p $PORT core.asgi:application
    envVars:
      - key: DEBUG
        value: false
      - key: ALLOWED_HOSTS
        fromService:
          name: sociallink-backend
          type: web
          property: host
      - key: DATABASE_URL
        fromDatabase:
          name: sociallink-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: sociallink-redis
          type: redis
          property: connectionString

  - type: worker
    name: sociallink-celery
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A core worker --loglevel=info --concurrency=2

databases:
  - name: sociallink-db
    databaseName: sociallink
    user: sociallink

  - name: sociallink-redis
    type: redis
```

**Free tier limits:** Web service spins down after 15 min inactivity (restarts in ~30s on next request).

---

## Method 6: Netlify (Frontend Only) + ngrok/Railway (Backend)

> Deploy React frontend permanently for free, keep backend local via ngrok.

### Deploy React to Netlify

```bash
cd frontend
npm run build
```

Install Netlify CLI:
```bash
npm install -g netlify-cli
netlify login
netlify deploy --prod --dir=dist
```

You get: `https://yourapp.netlify.app`

### Point Frontend at Your ngrok Backend

Create `frontend/.env.production`:
```env
VITE_API_URL=https://abc123.ngrok-free.app
VITE_WS_URL=wss://abc123.ngrok-free.app
```

Rebuild and redeploy:
```bash
npm run build
netlify deploy --prod --dir=dist
```

> **Problem:** ngrok URL changes every restart → you have to update Netlify env and redeploy each time. Use a paid ngrok fixed domain or Cloudflare Tunnel instead.

---

## Recommended Setup for Instagram Webhook Testing

The best free combo:

```
Instagram → Cloudflare Tunnel → localhost:8000 (Django) → Celery → Redis
```

```bash
# Terminal 1: Django
source venv/bin/activate
python manage.py runserver 8000

# Terminal 2: Celery worker
celery -A core worker --loglevel=info

# Terminal 3: Celery beat
celery -A core beat --loglevel=info

# Terminal 4: Cloudflare tunnel (permanent URL)
cloudflared tunnel run sociallink-dev
# OR quick temporary URL:
cloudflared tunnel --url http://localhost:8000
```

Register webhook:
```bash
python manage.py setup_webhook --url https://dev.yourdomain.com
```

---

## Django Settings Checklist for Any Tunnel

When you get a new tunnel URL, update these:

```python
# core/settings.py — already handles ngrok automatically in DEBUG mode
# For other tunnels, add to ALLOWED_HOSTS in .env:
ALLOWED_HOSTS=localhost,127.0.0.1,abc123.ngrok-free.app,dev.yourdomain.com

# Add to CORS_ALLOWED_ORIGINS:
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://your-tunnel-url.com",
]
```

For Cloudflare tunnels, also add wildcard to settings.py:
```python
if DEBUG:
    ALLOWED_HOSTS += [
        '.ngrok-free.app',
        '.trycloudflare.com',   # cloudflare quick tunnels
        '.loca.lt',             # localtunnel
    ]
```

---

## Summary: Which to Use When

| Scenario | Use |
|---|---|
| Testing Instagram webhooks locally right now | **ngrok** (already configured) |
| Need permanent free URL for webhooks | **Cloudflare Tunnel** |
| 5-min demo to someone | **localtunnel** |
| Staging environment for teammates | **Railway** or **Render** |
| Deploy frontend only, keep backend local | **Netlify** + ngrok |
| Full app testing with real database | **Railway** (easiest) |
