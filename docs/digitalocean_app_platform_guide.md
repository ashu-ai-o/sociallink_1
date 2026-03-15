# DigitalOcean App Platform Deployment Guide

DigitalOcean App Platform is a Platform-as-a-Service (PaaS). It works by connecting directly to your GitHub repository. Every time you push code to the `main` branch, DigitalOcean automatically builds your Docker image and updates your live servers with zero downtime.

To host your full architecture (Django Web, Celery Paid, Celery Free, Celery System), you simply define them as "Components" in the App Platform.

## Option 1: The UI Method (Easiest)

1. **Go to DigitalOcean > Apps > Create App**.
2. **Connect your GitHub account** and select the repository holding this codebase.
3. Keep the source directory as `/` and turn on **Autodeploy**.
4. DigitalOcean will automatically detect your `Dockerfile` and suggest creating a "Web Service".
5. **Add Components**: In the setup screen, click "Add Resource" to add your background workers.
   - **Resource 1 (Web):**
     - Type: Web Service
     - Run Command: `gunicorn core.wsgi:application --bind 0.0.0.0:8000`
     - Scaling: Set to 2-3 containers for redundancy.
   - **Resource 2 (Worker - Paid):**
     - Type: Worker
     - Run Command: `celery -A core worker -Q paid_high -P gevent -l info --autoscale=1000,10`
     - Scaling: Set as needed (e.g., 2 dedicated containers).
   - **Resource 3 (Worker - Free):**
     - Type: Worker
     - Run Command: `celery -A core worker -Q free_default -P gevent -l info --autoscale=500,10`
     - Scaling: Set higher if you have more volume of free users.
   - **Resource 4 (Worker - System):**
     - Type: Worker
     - Run Command: `celery -A core worker -Q system -P gevent -l info --autoscale=50,2`
6. **Databases**: Click "Add Database" in the same setup UI.
   - Choose **Managed PostgreSQL** and **Managed Redis**.
   - The App Platform will automatically inject the `DATABASE_URL` and `REDIS_URL` safely into your containers as environment variables!
7. **Environment Variables**: Click "Bulk Edit" in the UI environment variables section and paste your `.env` contents (like `OPENROUTER_API_KEYS`, `SECRET_KEY`, etc.).
8. **Click Launch!** Wait 5 minutes, and your entire infrastructure is live, load-balanced, and secured with SSL automatically.

---

## Option 2: The Infrastructure-as-Code Method (`app.yaml`)

Instead of clicking through the UI, you can place an `app.yaml` file in the root of your repository. When you create the app, DigitalOcean reads this file and configures everything instantly.

Here is what your `app.yaml` would look like for this 1000+ user architecture:

```yaml
name: sociallink-app
region: nyc3 # Pick the region closest to your users

# 1. The Managed Databases
databases:
  - name: sociallink-db
    engine: PG
    version: "15"
  - name: sociallink-redis
    engine: REDIS
    version: "7"

# 2. The Main Django Web Server
services:
  - name: web
    github:
      repo: your-username/sociallink_1
      branch: main
    # Tells DO how to start the HTTP server
    run_command: gunicorn core.wsgi:application --bind 0.0.0.0:8000
    # Auto-Scaling: Add more web servers if CPU hits 80%
    instance_count: 2 # Minimum servers
    instance_size_slug: basic-xs
    envs:
      - key: DATABASE_URL
        scope: RUN_AND_BUILD_TIME
        value: ${sociallink-db.DATABASE_URL}
      - key: REDIS_URL
        scope: RUN_AND_BUILD_TIME
        value: ${sociallink-redis.REDIS_URL}

# 3. The Background Workers
workers:
  - name: celery-paid
    github:
      repo: your-username/sociallink_1
      branch: main
    run_command: celery -A core worker -Q paid_high -P gevent -l info --autoscale=1000,10
    instance_count: 2
    instance_size_slug: basic-s
    envs:
      - key: DATABASE_URL
        value: ${sociallink-db.DATABASE_URL}
      - key: REDIS_URL
        value: ${sociallink-redis.REDIS_URL}

  - name: celery-free
    github:
      repo: your-username/sociallink_1
      branch: main
    run_command: celery -A core worker -Q free_default -P gevent -l info --autoscale=500,10
    instance_count: 4
    instance_size_slug: basic-s
    envs:
      - key: DATABASE_URL
        value: ${sociallink-db.DATABASE_URL}
      - key: REDIS_URL
        value: ${sociallink-redis.REDIS_URL}

  - name: celery-system
    github:
      repo: your-username/sociallink_1
      branch: main
    run_command: celery -A core worker -Q system -P gevent -l info --autoscale=50,2
    instance_count: 1
    instance_size_slug: basic-xs
    envs:
      - key: DATABASE_URL
        value: ${sociallink-db.DATABASE_URL}
      - key: REDIS_URL
        value: ${sociallink-redis.REDIS_URL}
```

### Why this is the easiest to manage:

1. **Auto-healing**: If your `celery-free` worker crashes because it ran out of memory, DigitalOcean instantly destroys it and spins up a brand new fresh container automatically. You don't have to SSH into a server to fix it.
2. **Zero-downtime deploys**: When you push new code to Github, DigitalOcean builds the new image in the background. It only shuts down the old containers _after_ the new containers are confirmed to be healthy and running. Users never see a 502 Bad Gateway.
3. **Database Security**: Your Database and Redis server are placed inside a private VPC network. They are inaccessible from the open public internet, keeping your user data secure.

## Scaling Terminology Explained

| Term                   | Meaning                                                                             | Why it matters                                                                  |
| :--------------------- | :---------------------------------------------------------------------------------- | :------------------------------------------------------------------------------ |
| **Instance Count**     | The number of identical copies of your code running.                                | Setting this to `2+` ensures your site stays online even if one server crashes. |
| **Horizontal Scaling** | Adding more instances (servers) instead of making one server bigger.                | Best for handling thousands of users across multiple CPUs.                      |
| **Vertical Scaling**   | Increasing the RAM/CPU of a single instance (Instance Size).                        | Good for heavy calculations, but limited by the maximum size of one machine.    |
| **Vertical + Horizontal Scaling** | Picking a strong "base" server size and then letting it autoscale more copies as needed. | The gold standard for 1000+ users. It ensures each worker is powerful enough for AI, while the count handles the crowd. |
| **Autoscale (Celery)** | Dynamically changing the number of active tasks based on how many are in the queue. | Saves money by only using power when there is actually work to do.              |

## Recommended Budget Starter Plan (To start cheap)

If you are just launching and want to keep costs minimal while still having enough power for Gevent workers:

1. **Web Service**: **Basic XS** ($5.00/mo) - 512MB RAM.
   - *Why?* It only handles webhooks. It doesn't need much RAM.
2. **Workers (Paid/Free)**: **Basic S** ($10.00/mo) - 1GB RAM.
   - *Why?* To handle 1000 green-threads (`gevent`), you need at least 1GB of RAM so the server doesn't "Out of Memory" crash when multiple AI tasks are running.
3. **Managed Database**: **Basic** ($15.00/mo) - 1 vCPU, 1GB RAM.
4. **Managed Redis**: **Basic** ($15.00/mo) - 1 vCPU, 1GB RAM.

**Total Launch Cost: ~$55.00/mo**

*Note: Once you hit 1000+ ACTUAL concurrent users, you should upgrade the WORKERS to the **Professional** tier ($20+/mo) to get dedicated CPUs, as the Basic tier shares CPU time with other people.*

## Why App Platform is safer than Droplets for 1000+ Users

| Scenario | App Platform | Droplets (VPS) |
| :--- | :--- | :--- |
| **Worker Crashes** | DO detects it and restarts a fresh container instantly. | Worker stays dead until you SSH in and restart it manually. |
| **Traffic Spike** | You increase `instance_count` in the UI to scale instantly. | You have to manually set up a new server and load balancer. |
| **SSL / Security** | SSL is automatic and managed. | You must set up and renew Certbot/LetsEncrypt yourself. |
| **Updates** | Zero-downtime rolling updates (automatic). | Site usually goes down for a few seconds during restart. |

## Setting up your Own Domain

DigitalOcean App Platform makes using your own domain very easy:

1.  **In the App Dashboard**: Go to **Settings** > **Domains** > **Add Domain**.
2.  **Type your domain**: (e.g., `yourapp.com`).
3.  **DigitalOcean will give you a CNAME record**:
    - Log into your domain registrar (GoDaddy, Namecheap, etc.).
    - Create a CNAME record pointing to your DigitalOcean app URL.
4.  **Wait for SSL**: DigitalOcean will automatically see the link, issue a free SSL certificate, and secure your site within minutes.

*Tip: If you use DigitalOcean's Nameservers for your domain, the setup is even easier—it will configure the DNS records for you automatically with one click!*

## Connecting your Netlify Frontend

Since your frontend is on Netlify and your backend is on DigitalOcean, you have a **Decoupled Architecture**. Here is how to make them talk to each other:

### 1. The Subdomain Strategy
- **Main Domain (`yourdomain.com`):** Points to Netlify (Frontend).
- **Subdomain (`api.yourdomain.com`):** Points to DigitalOcean App Platform (Backend).

### 2. Configure CORS in Django
I have already added the necessary code to your `core/settings.py`. 
- When you deploy, make sure to set the environment variable `CORS_ALLOWED_ORIGINS` to `https://your-netlify-app-name.netlify.app`.
- If you have a custom domain on Netlify, use `https://yourdomain.com` instead.

### 3. Update your Frontend Code
In your frontend code (e.g., in your `api.js` or `constants.js`), update the base URL:
```javascript
// BEFORE (Local Development)
const API_BASE_URL = "http://localhost:8000";

// AFTER (Production)
const API_BASE_URL = "https://api.yourdomain.com";
```
