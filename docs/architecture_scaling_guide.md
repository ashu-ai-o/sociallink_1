# Architecture Guide: Hosting Django + Celery for 1000+ Concurrent Users

When scaling to 1000+ concurrent users, running everything on a single server with `supervisor` becomes a massive bottleneck. A single server will run out of CPU, RAM, or network bandwidth.

To handle true enterprise scale, you must move to a **Distributed Architecture** using **Docker**.

## Why Docker over Supervisor?

**Supervisor** is designed to manage multiple processes on a _single machine_. If that machine dies, all your workers die.
**Docker** (specifically with an orchestrator like Docker Swarm or Kubernetes) allows you to package your Celery workers into containers and spread them across _multiple machines_.

## The Recommended Scalable Architecture

To support 1000+ concurrent active automation accounts, you need to separate your services into different physical (or virtual) servers.

### 1. The Load Balancer (Nginx / HAProxy)

- **Role**: Receives all incoming HTTP requests (like webhooks from Instagram) and distributes them evenly across your Web Servers.

### 2. The Web Servers (Django + Gunicorn)

- **Role**: Handles immediate HTTP responses and webhook ingestion.
- **Scale**: Run 3 to 10 Docker containers of your Django app. They _only_ accept webhooks, save triggers to the database, and dispatch tasks to Celery. They do zero heavy lifting.

### 3. The Message Broker (Redis Cluster / Managed Redis)

- **Role**: The central nervous system. Web servers drop task IDs here, and Celery workers pick them up.
- **Scale**: Do **not** host this yourself on a standard droplet. Use DigitalOcean Managed Redis or AWS ElastiCache. This ensures the broker never crashes under the weight of 10,000+ queued tasks.

### 4. The Worker Nodes (Celery + Docker)

- **Role**: The heavy lifters. These servers do the actual API calls to Instagram and OpenRouter.
- **Scale**: This is where you scale horizontally. You can have Server A processing the `paid_high` queue, Server B processing the `free_default` queue, and Server C processing the `system` queue.
- _If the `free_default` queue gets backed up, you simply spin up Server D and point it to the free queue._

### 5. The Database (Managed PostgreSQL)

- **Role**: Stores users, billing, and logs.
- **Scale**: Use a Managed Database with Connection Pooling (PgBouncer). 1000+ users means 1000+ Celery workers trying to read/write to the DB simultaneously. A standard DB will crash from "connection exhaustion" without PgBouncer.

---

## Example `docker-compose.prod.yml`

This is the standard way to define your infrastructure. You deploy this file to a Docker Swarm or Kubernetes cluster.

```yaml
version: "3.8"

services:
  web:
    build: .
    command: gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
    ports:
      - "8000:8000"
    env_file: .env
    deploy:
      replicas: 3 # Run 3 web servers

  celery_paid:
    build: .
    command: celery -A core worker -Q paid_high --autoscale=1000,10 -l info
    env_file: .env
    deploy:
      replicas: 2 # Run 2 paid worker containers

  celery_free:
    build: .
    command: celery -A core worker -Q free_default --autoscale=1000,10 -l info
    env_file: .env
    deploy:
      replicas: 4 # Run 4 free worker containers to handle bulk

  celery_system:
    build: .
    command: celery -A core worker -Q system --autoscale=50,2 -l info
    env_file: .env

  celery_beat:
    build: .
    command: celery -A core beat -l info
    env_file: .env
    deploy:
      replicas: 1 # ONLY EVER RUN EXACTLY 1 BEAT SCHEDULER
```

## How to Deploy This (The "Right" Way)

1. **DigitalOcean App Platform**: Easiest. You push your code to GitHub, tell DigitalOcean your `docker-compose` commands, and they handle the servers, scaling, and load balancing automatically.
2. **Kubernetes (DOKS)**: The industry standard but very complex. You create a cluster of servers, give it your Docker images, and configure "Horizontal Pod Autoscalers" (HPA) to automatically add more servers if CPU usage hits 80%.
3. **Docker Swarm**: The middle ground. You rent 5 basic Linux droplets on DigitalOcean, link them together in a "Swarm", and run `docker stack deploy`. Docker natively spreads the containers across the 5 droplets.

### Verdict for you:

Start with **DigitalOcean App Platform** or **AWS Elastic Beanstalk**. It uses Docker under the hood but hides the server management from you, allowing you to easily say "Give me 5 Celery Paid Workers" via a UI slider when traffic spikes.
