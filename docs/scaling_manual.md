# Scaling Manual: Handling Traffic without Downtime

This manual explains how to scale your SocialLink infrastructure from a single $12/mo Droplet to a high-traffic system while keeping the server online 24/7.

## 1. The Challenge of "Standard" Scaling
Normally, to give a Droplet more RAM/CPU, you must **shutdown** the server for 2-3 minutes. This causes downtime. 

To avoid this, we use the following strategies:

---

## 2. Strategy A: "Soft Scaling" (Zero Server Downtime)
If your Droplet still has free RAM but tasks are queuing up, you can increase Celery concurrency **without rebooting the server**.

### How to do it:
1. SSH into your server.
2. Edit the `--autoscale` values in your `docker-compose.prod.yml`.
3. Run this command:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --no-deps celery_worker
   ```
   **What happens?** Docker will restart ONLY the Celery worker container. This takes ~5 seconds. Your Website, Database, and Redis remain online and untouched.

---

## 3. Strategy B: "Horizontal Scaling" (True Zero Downtime)
This is the only way to scale your hardware (RAM/CPU) without ever stopping the site.

### The Workflow:
1. **Create a Second Droplet**: Spin up a new $12/mo Droplet.
2. **Add a Load Balancer**: Use a DigitalOcean Load Balancer ($12/mo) or setup Nginx on a separate small node.
3. **Connect Both**: Point the Load Balancer to both Droplets.
4. **Result**: You now have 2x the power. If you need to upgrade "Droplet A", the traffic simply flows to "Droplet B" while A is being resized.

---

## 4. Strategy C: Moving to App Platform
If traffic becomes unpredictable (spikes every hour), the manual Droplet approach becomes exhausting. 

1. Push your `app.yaml` to GitHub.
2. DigitalOcean App Platform will handle the **Horizontal Scaling** for you.
3. It creates new containers in the background and only swaps them once they are healthy. 

## Comparison Table

| Scaling Task | Droplet Method | Downtime? | App Platform Method | Downtime? |
| :--- | :--- | :--- | :--- | :--- |
| **Increase Workers**| Restart Container | ~5 Sec | Slider in UI | **Zero** |
| **Add RAM/CPU** | Resize Droplet | **~3 Min**| Change Instance Type| **Zero** |
| **Deploy Code** | Git Pull + Restart | ~10 Sec | Push to GitHub | **Zero** |

## Recommendation for Traffic Spikes
1. Monitor your RAM using `htop` on the server.
2. If RAM is < 70%, use **Strategy A** (Increase autoscale limits).
3. If RAM is > 90%, you **must** upgrade the Droplet (Strategy B or C).
