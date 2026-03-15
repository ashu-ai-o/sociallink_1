# CI/CD Pipeline Guide (GitHub Actions)

This guide explains how to set up automated deployments for your SocialLink project using GitHub Actions and your DigitalOcean Droplet.

## 1. How it Works
Every time you push code to the `main` branch:
1. GitHub Actions will connect to your DigitalOcean Droplet via SSH.
2. It will pull the latest code from your repository.
3. It will rebuild the Docker containers using `docker-compose.prod.yml`.
4. It will run migrations and collect static files automatically.

## 2. Setup GitHub Secrets
Go to your GitHub Repository > **Settings** > **Secrets and variables** > **Actions** and add the following secrets:

| Secret Name | Description |
| :--- | :--- |
| `DROPLET_IP` | The IP address of your DigitalOcean Droplet. |
| `DROPLET_USER` | Usually `root`. |
| `SSH_PRIVATE_KEY` | Your SSH private key (to log in without a password). |
| `ENV_FILE` | The entire content of your production `.env` file. |

## 3. The Deployment Workflow
The deployment logic is defined in `.github/workflows/deploy.yml`. 

### Key Commands executed during deployment:
```bash
cd /var/www/sociallink
git pull origin main
echo "$ENV_FILE" > .env
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
```

## 4. Triggering a Deploy
Simply commit your changes and push to GitHub:
```bash
git add .
git commit -m "update features"
git push origin main
```
You can monitor the progress in the **Actions** tab of your GitHub repository.
