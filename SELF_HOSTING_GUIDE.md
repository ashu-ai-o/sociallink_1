# Self-Hosting Guide — Run SocialLink on Your Own Server

No cloud platforms. No managed services. Your machine, your rules.

Stack: **Django 6 + Daphne (ASGI) + Celery + Redis + PostgreSQL + React (Vite)**

---

## Choose Your Method

| Method | Best For | Cost | Difficulty |
|---|---|---|---|
| [1. VPS Bare Metal (Nginx + systemd)](#method-1-vps--dedicated-server-bare-metal) | Production, always-on | VPS rent | Medium |
| [2. Docker Compose on Your Server](#method-2-docker-compose-on-your-server) | Easiest production setup | VPS rent | Easy |
| [3. Home Server + Cloudflare Tunnel](#method-3-home-server--cloudflare-tunnel-no-static-ip) | Home PC / no static IP | Free | Easy |
| [4. Home Server + Port Forwarding](#method-4-home-server--port-forwarding) | Home PC + static IP | Free | Medium |

---

## Method 1: VPS / Dedicated Server (Bare Metal)

> Best production setup. Works on any Ubuntu/Debian VPS (Hetzner, Contabo, any cheap VPS).

### 1.1 — Server Prerequisites

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip \
    postgresql postgresql-contrib redis-server nginx nodejs npm git curl
```

### 1.2 — Clone & Setup Project

```bash
cd /var/www
git clone <your-repo-url> sociallink
cd sociallink

# Python virtualenv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install daphne gunicorn

# Frontend build
cd frontend
npm install
npm run build          # outputs to frontend/dist/
cd ..
```

### 1.3 — PostgreSQL Database

```bash
sudo -u postgres psql
```
```sql
CREATE DATABASE sociallink_db;
CREATE USER sociallink_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE sociallink_db TO sociallink_user;
\q
```

### 1.4 — Environment File

Create `/var/www/sociallink/.env`:

```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DATABASE_URL=postgresql://sociallink_user:yourpassword@localhost:5432/sociallink_db
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_HOST=127.0.0.1

SECRET_KEY=your-very-long-random-secret-key

INSTAGRAM_WEBHOOK_VERIFY_TOKEN=your_verify_token
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
INSTAGRAM_CLIENT_SECRET=your_ig_secret

BACKEND_URL=https://yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

### 1.5 — Django Setup

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 1.6 — systemd Services

**Daphne (Django ASGI server):**

```bash
sudo nano /etc/systemd/system/sociallink-daphne.service
```
```ini
[Unit]
Description=SocialLink Daphne ASGI Server
After=network.target postgresql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/sociallink
EnvironmentFile=/var/www/sociallink/.env
ExecStart=/var/www/sociallink/venv/bin/daphne \
    -b 127.0.0.1 \
    -p 8000 \
    core.asgi:application
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Celery Worker:**

```bash
sudo nano /etc/systemd/system/sociallink-celery.service
```
```ini
[Unit]
Description=SocialLink Celery Worker
After=network.target redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/sociallink
EnvironmentFile=/var/www/sociallink/.env
ExecStart=/var/www/sociallink/venv/bin/celery \
    -A core worker \
    --loglevel=info \
    --concurrency=4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Celery Beat (Scheduler):**

```bash
sudo nano /etc/systemd/system/sociallink-celerybeat.service
```
```ini
[Unit]
Description=SocialLink Celery Beat Scheduler
After=network.target redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/sociallink
EnvironmentFile=/var/www/sociallink/.env
ExecStart=/var/www/sociallink/venv/bin/celery \
    -A core beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and start all services:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable sociallink-daphne sociallink-celery sociallink-celerybeat
sudo systemctl start sociallink-daphne sociallink-celery sociallink-celerybeat

# Verify
sudo systemctl status sociallink-daphne
sudo journalctl -u sociallink-daphne -f
```

### 1.7 — Nginx Config

```bash
sudo nano /etc/nginx/sites-available/sociallink
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 20M;

    # React frontend (built static files)
    root /var/www/sociallink/frontend/dist;
    index index.html;

    # Django static files
    location /static/ {
        alias /var/www/sociallink/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Django media files
    location /media/ {
        alias /var/www/sociallink/media/;
    }

    # WebSocket connections (Django Channels)
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Django API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Django admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # React SPA — catch-all for frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/sociallink /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 1.8 — Free SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
# Auto-renewal is set up automatically
```

### 1.9 — File Permissions

```bash
sudo chown -R www-data:www-data /var/www/sociallink
sudo chmod -R 755 /var/www/sociallink
```

---

## Method 2: Docker Compose on Your Server

> Easiest way — works on any server with Docker installed.

### 2.1 — Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in
```

### 2.2 — Create `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: sociallink_db
      POSTGRES_USER: sociallink_user
      POSTGRES_PASSWORD: yourpassword

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  web:
    build: .
    restart: always
    command: daphne -b 0.0.0.0 -p 8000 core.asgi:application
    volumes:
      - static_files:/app/staticfiles
      - media_files:/app/media
    env_file: .env
    environment:
      DATABASE_URL: postgresql://sociallink_user:yourpassword@postgres:5432/sociallink_db
      REDIS_URL: redis://redis:6379/0
      REDIS_HOST: redis
    depends_on:
      - postgres
      - redis

  celery_worker:
    build: .
    restart: always
    command: celery -A core worker --loglevel=info --concurrency=4
    env_file: .env
    environment:
      DATABASE_URL: postgresql://sociallink_user:yourpassword@postgres:5432/sociallink_db
      REDIS_URL: redis://redis:6379/0
      REDIS_HOST: redis
    depends_on:
      - postgres
      - redis

  celery_beat:
    build: .
    restart: always
    command: celery -A core beat --loglevel=info
    env_file: .env
    environment:
      DATABASE_URL: postgresql://sociallink_user:yourpassword@postgres:5432/sociallink_db
      REDIS_URL: redis://redis:6379/0
      REDIS_HOST: redis
    depends_on:
      - postgres
      - redis

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_files:/app/staticfiles:ro
      - media_files:/app/media:ro
      - ./ssl:/etc/nginx/ssl:ro          # put your certs here
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  static_files:
  media_files:
```

### 2.3 — Create `Dockerfile`

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt daphne

# Build React frontend
COPY frontend/package*.json frontend/
RUN cd frontend && npm install
COPY frontend/ frontend/
RUN cd frontend && npm run build

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
```

### 2.4 — Deploy

```bash
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Check logs
docker compose -f docker-compose.prod.yml logs -f web celery_worker
```

---

## Method 3: Home Server + Cloudflare Tunnel (No Static IP)

> Run on your home PC / Raspberry Pi. **No port forwarding. No static IP needed.**
> Cloudflare acts as the middleman — completely free.

### 3.1 — Requirements
- A domain name pointed to Cloudflare nameservers (free)
- Your app running locally on port 8000

### 3.2 — Install cloudflared

```bash
# Linux (x64)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
```

### 3.3 — Authenticate & Create Tunnel

```bash
cloudflared tunnel login          # opens browser, select your domain
cloudflared tunnel create sociallink
```

Copy the tunnel ID shown (e.g. `abc123de-...`).

### 3.4 — Tunnel Config

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: abc123de-REPLACE-WITH-YOUR-TUNNEL-ID
credentials-file: /home/youruser/.cloudflared/abc123de-REPLACE.json

ingress:
  - hostname: yourdomain.com
    service: http://localhost:8000
    originRequest:
      noTLSVerify: false
  - service: http_status:404
```

### 3.5 — Point DNS to Tunnel

```bash
cloudflared tunnel route dns sociallink yourdomain.com
```

### 3.6 — Run as systemd Service (auto-start on boot)

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### 3.7 — Start Your App

```bash
# Terminal 1: Django
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000    # or use daphne for production

# Terminal 2: Celery worker
celery -A core worker --loglevel=info

# Terminal 3: Celery beat
celery -A core beat --loglevel=info
```

Your app is now live at `https://yourdomain.com` with **automatic HTTPS** via Cloudflare.

> **Meta Webhook** — use `https://yourdomain.com/api/webhooks/instagram/` as the callback URL. Works perfectly with Cloudflare Tunnel.

---

## Method 4: Home Server + Port Forwarding

> For home servers with a **static IP** (or use a free DDNS service).

### 4.1 — Router Port Forwarding

In your router settings, forward:
- Port `80` → your server's local IP (e.g. `192.168.1.100`)
- Port `443` → your server's local IP

### 4.2 — No Static IP? Use Free DDNS

Services that give you a free domain that tracks your changing IP:
- **DuckDNS** — `yourname.duckdns.org` (free, recommended)
- **No-IP** — `yourname.ddns.net`

**DuckDNS auto-update cron:**
```bash
# Get your token from duckdns.org
echo "*/5 * * * * curl -s 'https://www.duckdns.org/update?domains=yourname&token=YOUR_TOKEN&ip=' > /dev/null" | crontab -
```

### 4.3 — Then Follow Method 1

Once port forwarding is set up and DNS is pointing to your IP, follow the same [Nginx + systemd steps from Method 1](#method-1-vps--dedicated-server-bare-metal) — just run them on your home machine.

---

## Common Post-Setup Steps (All Methods)

### Update `.env` for Production

```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
BACKEND_URL=https://yourdomain.com
```

### Register Instagram Webhook

```bash
python manage.py setup_webhook --url https://yourdomain.com
```

### Check Everything is Running

```bash
# systemd (Methods 1 & 4)
sudo systemctl status sociallink-daphne sociallink-celery sociallink-celerybeat

# Docker (Method 2)
docker compose -f docker-compose.prod.yml ps

# Cloudflare (Method 3)
sudo systemctl status cloudflared
cloudflared tunnel info sociallink
```

### Verify Webhook Works

```bash
curl -X GET "https://yourdomain.com/api/webhooks/instagram/?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test123"
# Should return: test123
```

---

## Recommended Method by Situation

| Situation | Use |
|---|---|
| Have a cheap VPS ($4-6/month Hetzner/Contabo) | **Method 1 or 2** |
| Old PC / Raspberry Pi at home, want it free | **Method 3 (Cloudflare Tunnel)** |
| Home server, already have static IP | **Method 4** |
| Want simplest setup, have Docker | **Method 2** |
| Want full control, no Docker overhead | **Method 1** |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ALLOWED_HOSTS` error | Add your domain to `ALLOWED_HOSTS` in `.env` |
| WebSocket not connecting | Check Nginx `location /ws/` block has `Upgrade` headers |
| Static files not loading | Run `python manage.py collectstatic` and check Nginx `alias` path |
| Celery tasks not running | Check Redis is running: `redis-cli ping` → should return `PONG` |
| 502 Bad Gateway | Daphne isn't running — check `journalctl -u sociallink-daphne` |
| SSL cert issues | Run `certbot renew --dry-run` to test auto-renewal |
| Cloudflare tunnel offline | `sudo systemctl restart cloudflared` |
