# Celery Supervisor Setup Guide for DigitalOcean (Ubuntu)

This guide shows how to deploy your Django Celery workers to a Linux server (like DigitalOcean Ubuntu) using `supervisor` to keep them running in the background automatically, and restart them if they crash.

## 1. Install Supervisor

Log into your DigitalOcean droplet via SSH and install supervisor:

```bash
sudo apt-get update
sudo apt-get install supervisor
```

## 2. Create Celery Worker Config Files

Supervisor uses configuration files located in `/etc/supervisor/conf.d/`.
You will create exactly 3 files, one for each queue: `paid_high`, `free_default`, and `system`.

I'm assuming your project is located at `/var/www/sociallink_1` and your python virtual environment is at `/var/www/sociallink_1/env`. Change these paths if yours are different!

### A. Paid Queue Worker

Create the file:
```bash
sudo nano /etc/supervisor/conf.d/celery_paid.conf
```

Paste this configuration:
```ini
[program:celery_paid]
# The command to start the Celery worker for the paid_high queue
command=/var/www/sociallink_1/env/bin/celery -A core worker -Q paid_high -l info --autoscale=1000,10

# Directory where your Django project lives
directory=/var/www/sociallink_1

# Run as an unprivileged user (change 'ubuntu' if your user is 'root' or 'www-data')
user=ubuntu
numprocs=1

# Automatically start exactly when the server boots up
autostart=true
# Automatically restart if it crashes
autorestart=true
startsecs=10

# Restart quickly if it fails
stopwaitsecs=600
killasgroup=true

# Log files
stdout_logfile=/var/log/celery/paid_worker.log
stderr_logfile=/var/log/celery/paid_worker_error.log
```

### B. Free Queue Worker

Create the file:
```bash
sudo nano /etc/supervisor/conf.d/celery_free.conf
```

Paste this configuration:
```ini
[program:celery_free]
command=/var/www/sociallink_1/env/bin/celery -A core worker -Q free_default -l info --autoscale=500,10
directory=/var/www/sociallink_1
user=ubuntu
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
stdout_logfile=/var/log/celery/free_worker.log
stderr_logfile=/var/log/celery/free_worker_error.log
```

### C. System Queue Worker

Create the file:
```bash
sudo nano /etc/supervisor/conf.d/celery_system.conf
```

Paste this configuration:
```ini
[program:celery_system]
command=/var/www/sociallink_1/env/bin/celery -A core worker -Q system -l info --autoscale=50,2
directory=/var/www/sociallink_1
user=ubuntu
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
stdout_logfile=/var/log/celery/system_worker.log
stderr_logfile=/var/log/celery/system_worker_error.log
```


## 3. Create the Log Directory

Before starting the workers, create the directory where the logs will be stored and give correct permissions:

```bash
sudo mkdir -p /var/log/celery
# Change 'ubuntu' to the user you specified in the config files above
sudo chown -R ubuntu:ubuntu /var/log/celery
```


## 4. Start the Workers

Now tell supervisor to read the new configuration files and start the celery workers:

```bash
# Reread the configurations
sudo supervisorctl reread

# Add the new configurations to the active process list
sudo supervisorctl update

# Check the status to verify they are running!
sudo supervisorctl status
```

You should see an output similar to this:
```
celery_free                      RUNNING   pid 12345, uptime 0:00:15
celery_paid                      RUNNING   pid 12346, uptime 0:00:15
celery_system                    RUNNING   pid 12347, uptime 0:00:15
```

## How to manage the workers later

If you ever deploy new code or make changes to `tasks.py`, you MUST restart the celery workers so they pick up the new python code:

```bash
# Restart all celery workers
sudo supervisorctl restart celery_paid celery_free celery_system

# View live logs if something goes wrong
tail -f /var/log/celery/paid_worker.log
```
