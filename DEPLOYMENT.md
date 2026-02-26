# ABEM — Production Deployment Guide

> **Audience:** DevOps engineers and developers responsible for deploying the ABEM platform to production.
> **Stack:** Django 4.2 · PostgreSQL 16 · Redis 7 · Celery · React (Nginx) · Flutter (Android/iOS)

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [External Services Audit](#2-external-services-audit)
3. [Server Provisioning](#3-server-provisioning)
4. [Repository Setup](#4-repository-setup)
5. [Environment Variables](#5-environment-variables)
6. [Docker — Production Deployment](#6-docker--production-deployment)
7. [Manual (Non-Docker) Deployment](#7-manual-non-docker-deployment)
8. [Database Setup & Migrations](#8-database-setup--migrations)
9. [Superuser Creation](#9-superuser-creation)
10. [Static & Media Files](#10-static--media-files)
11. [Nginx & TLS / HTTPS](#11-nginx--tls--https)
12. [Celery (Background Tasks)](#12-celery-background-tasks)
13. [Frontend Build & Deployment](#13-frontend-build--deployment)
14. [Mobile (Flutter) Release](#14-mobile-flutter-release)
15. [CI/CD — GitHub Actions](#15-cicd--github-actions)
16. [Monitoring & Logging](#16-monitoring--logging)
17. [Post-Deployment Smoke Tests](#17-post-deployment-smoke-tests)
18. [Rollback Procedure](#18-rollback-procedure)
19. [Security Hardening Checklist](#19-security-hardening-checklist)
20. [Useful References](#20-useful-references)

---

## 1. Prerequisites

### Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU      | 2 vCPUs | 4 vCPUs    |
| RAM      | 2 GB    | 4 GB        |
| Disk     | 20 GB SSD | 50 GB SSD |
| OS       | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

### Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Docker & Docker Compose (recommended installation method)
# Reference: https://docs.docker.com/engine/install/ubuntu/
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to the docker group (avoid sudo on every command)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version          # Docker version 26.x.x
docker compose version    # Docker Compose version v2.x.x
```

### Domain & DNS

Before deployment, ensure:
- A domain name is pointed at your server's IP (e.g. `abem.yourdomain.com`)
- An `A` record for the root domain and a `CNAME` or `A` record for `www` are configured
- DNS propagation is complete (`dig abem.yourdomain.com` returns your server IP)

**Reference:** [Cloudflare DNS setup guide](https://developers.cloudflare.com/dns/manage-dns-records/how-to/create-dns-records/)

---

## 2. External Services Audit

ABEM uses a mix of fully open-source tools (self-hostable, zero cost) and
third-party SaaS services.  This section identifies every external dependency,
whether it is required or optional, and provides a **fully open-source
self-hosted alternative** for each commercial service.

### 2.1 Core Stack — 100% Open Source

Every component below is free, self-hosted, and requires no external account.

| Component | License | Notes |
|-----------|---------|-------|
| Django 4.2 | BSD-3 | Backend API framework |
| Django REST Framework | BSD-2 | REST layer |
| PostgreSQL 16 | PostgreSQL License | Primary database |
| Redis 7 | BSD-3 | Celery broker & cache |
| Celery 5 | BSD-3 | Background task queue |
| Nginx 1.27 | BSD-2 | Reverse proxy & SPA server |
| React + Vite | MIT | Web frontend |
| Flutter 3 | BSD-3 | Mobile (Android & iOS) |
| WhiteNoise | MIT | Static file serving |
| Let's Encrypt / Certbot | Apache 2.0 | Free TLS certificates |
| Docker & Docker Compose | Apache 2.0 | Containerisation |
| drf-spectacular | BSD-3 | OpenAPI / Swagger docs |

### 2.2 Commercial / Third-Party Services

Four external SaaS services are currently configured.  **None of them block a
basic deployment** — each has a fully open-source self-hosted replacement
documented below.

| Service | Purpose | Commercial? | Free Tier | Required for launch? |
|---------|---------|-------------|-----------|----------------------|
| **Cloudinary** | Media file storage (uploads, images) | Yes (proprietary) | 25 GB / 25 GB bandwidth/mo | **No** — MinIO replaces it |
| **Firebase FCM** | Push notifications to mobile devices | Google (free) | Unlimited | Partial — unavoidable for native Android/iOS push; replaceable for web |
| **Sentry** (cloud) | Error tracking & alerting | Yes (open-core) | 5k events/mo | **No** — GlitchTip replaces it |
| **Gmail SMTP** | Transactional email (notifications) | Google (free) | 500 msgs/day | **No** — Postfix replaces it |

> **Mobile stores** — Google Play Store (US $25 one-time) and Apple App Store
> (US $99/year) are **platform requirements** for official app distribution.
> There is no open-source equivalent; direct APK sideloading is the only
> alternative for Android.

---

### 2.3 Open-Source Alternative: MinIO (replaces Cloudinary)

[MinIO](https://min.io/) is an S3-compatible self-hosted object store.
Django's `django-storages` + `boto3` already installed connect to it with
a one-line config change.

#### Add MinIO to docker-compose.prod.yml

```yaml
  minio:
    image: minio/minio:latest
    restart: always
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"   # S3 API
      - "9001:9001"   # Web console

volumes:
  minio_data:
```

#### Create the media bucket (one-time)

```bash
# Install mc (MinIO client)
curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc && sudo mv mc /usr/local/bin/

# Configure alias
mc alias set local http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

# Create the bucket and make it publicly readable
mc mb local/abem-media
mc anonymous set download local/abem-media
```

#### Django settings — switch to MinIO

In `.env.prod` replace the Cloudinary block with:

```bash
# MinIO (S3-compatible)
AWS_ACCESS_KEY_ID=<MINIO_ROOT_USER>
AWS_SECRET_ACCESS_KEY=<MINIO_ROOT_PASSWORD>
AWS_STORAGE_BUCKET_NAME=abem-media
AWS_S3_ENDPOINT_URL=http://minio:9000       # internal Docker network
AWS_S3_CUSTOM_DOMAIN=abem.yourdomain.com:9000
AWS_DEFAULT_ACL=public-read
AWS_QUERYSTRING_AUTH=False
```

In `config/settings/production.py` (or `base.py`) add:

```python
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
```

**Reference:** [django-storages S3 docs](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html) · [MinIO quickstart](https://min.io/docs/minio/linux/index.html)

---

### 2.4 Open-Source Alternative: ntfy (replaces Firebase FCM for web / in-app)

[ntfy](https://ntfy.sh/) is a self-hosted push notification server (MIT
license).  It handles **web-push and in-app notifications** without any Google
dependency.

> **Important:** Android native push (displayed in the system notification
> shade while the app is closed) **still requires FCM at the OS level** —
> this is an Android platform constraint, not a library choice.  ntfy has an
> [Android app](https://f-droid.org/packages/io.heckel.ntfy/) on F-Droid that
> routes through a self-hosted server, bypassing FCM entirely, but users must
> install that app separately.

#### Add ntfy to docker-compose.prod.yml

```yaml
  ntfy:
    image: binwiederhier/ntfy:latest
    restart: always
    command: serve
    environment:
      NTFY_BASE_URL: https://ntfy.yourdomain.com
      NTFY_UPSTREAM_BASE_URL: https://ntfy.sh   # relay for FCM-free Android push
    volumes:
      - ntfy_data:/var/lib/ntfy
    ports:
      - "8080:80"

volumes:
  ntfy_data:
```

#### Send a notification from Django (Celery task)

```python
import requests

def send_push_notification(topic: str, title: str, message: str):
    requests.post(
        f"http://ntfy:80/{topic}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": "default"},
    )
```

**Reference:** [ntfy documentation](https://docs.ntfy.sh/) · [ntfy self-hosting guide](https://docs.ntfy.sh/install/)

---

### 2.5 Open-Source Alternative: GlitchTip (replaces Sentry cloud)

[GlitchTip](https://glitchtip.com/) is a Sentry-compatible open-source error
tracker (MIT license).  It accepts the same Sentry SDK and DSN format — no
code changes required.

#### Add GlitchTip to docker-compose.prod.yml

```yaml
  glitchtip_db:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_DB: glitchtip
      POSTGRES_USER: glitchtip
      POSTGRES_PASSWORD: ${GLITCHTIP_DB_PASSWORD}
    volumes:
      - glitchtip_data:/var/lib/postgresql/data

  glitchtip:
    image: glitchtip/glitchtip:latest
    restart: always
    depends_on:
      - glitchtip_db
      - redis
    environment:
      DATABASE_URL: postgres://glitchtip:${GLITCHTIP_DB_PASSWORD}@glitchtip_db/glitchtip
      SECRET_KEY: ${GLITCHTIP_SECRET_KEY}
      EMAIL_URL: smtp://user:pass@mail:25
      GLITCHTIP_DOMAIN: https://glitchtip.yourdomain.com
      DEFAULT_FROM_EMAIL: errors@yourdomain.com
    ports:
      - "8080:8080"

volumes:
  glitchtip_data:
```

#### Point the Sentry SDK at GlitchTip

In `.env.prod`, change the DSN to your GlitchTip project DSN:

```bash
SENTRY_DSN=https://<key>@glitchtip.yourdomain.com/<project-id>
```

No change to `config/settings/production.py` — the existing `sentry_sdk.init()` call works as-is.

**Reference:** [GlitchTip self-hosting docs](https://glitchtip.com/documentation/install) · [GlitchTip Docker Compose guide](https://glitchtip.com/documentation/install#docker-compose)

---

### 2.6 Open-Source Alternative: Postfix + OpenDKIM (replaces Gmail SMTP)

[Postfix](http://www.postfix.org/) is a battle-tested self-hosted mail
transfer agent.  Combined with OpenDKIM (email signing) it handles
transactional email without any Google dependency.

```bash
sudo apt install -y postfix opendkim opendkim-tools

# Configure as "Internet Site" during postfix setup
sudo postconf -e "myhostname = mail.yourdomain.com"
sudo postconf -e "smtp_use_tls = yes"

# Generate DKIM key pair
sudo mkdir -p /etc/opendkim/keys/yourdomain.com
sudo opendkim-genkey -b 2048 -d yourdomain.com \
  -D /etc/opendkim/keys/yourdomain.com -s mail -v

# Add the public key to your DNS as a TXT record
# (shown in: /etc/opendkim/keys/yourdomain.com/mail.txt)
```

In `.env.prod`:

```bash
EMAIL_HOST=localhost
EMAIL_PORT=25
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

> **Easier alternative:** [Brevo](https://www.brevo.com/) (formerly Sendinblue) offers 300 free emails/day on their free plan with standard SMTP — no self-hosting required.

**Reference:** [Postfix documentation](http://www.postfix.org/documentation.html) · [OpenDKIM setup guide](http://www.opendkim.org/opendkim-README)

---

### 2.7 Summary — Fully Open-Source Deployment

To deploy ABEM **without any commercial account**, use:

| Role | Replace | With |
|------|---------|------|
| Media storage | Cloudinary | MinIO |
| Push notifications (web) | Firebase FCM | ntfy |
| Error tracking | Sentry cloud | GlitchTip |
| Email | Gmail SMTP | Postfix + OpenDKIM |
| Source control | GitHub | Gitea (self-hosted) |
| CI/CD | GitHub Actions | Woodpecker CI (works with Gitea) |

The only unavoidable platform costs are:
- **Google Play Store** — $25 one-time registration fee
- **Apple App Store** — $99/year Apple Developer Program membership

---

## 3. Server Provisioning

Recommended cloud providers:

| Provider | Plan | Notes |
|----------|------|-------|
| [DigitalOcean](https://docs.digitalocean.com/products/droplets/quickstart/) | Basic Droplet — 2 vCPU / 4 GB | `$24/mo`, easiest setup |
| [AWS EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html) | t3.medium | Production-grade, more complex |
| [Hetzner Cloud](https://docs.hetzner.com/cloud/servers/getting-started/creating-a-server/) | CX22 — 2 vCPU / 4 GB | `€5.08/mo`, excellent price/performance |
| [Vultr](https://www.vultr.com/docs/deploy-a-new-server/) | Regular Cloud Compute 2 vCPU / 4 GB | `$24/mo` |

### Firewall Rules (UFW)

```bash
sudo ufw enable
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP (redirects to HTTPS)
sudo ufw allow 443/tcp     # HTTPS
sudo ufw status
```

---

## 4. Repository Setup

```bash
# Clone the repository
git clone https://github.com/<your-org>/abem.git /opt/abem
cd /opt/abem

# (Optional) Switch to a specific release tag
git checkout v1.0.0
```

---

## 5. Environment Variables

Create the production environment file from the example:

```bash
cp .env.example .env.prod
nano .env.prod     # or: vim .env.prod
```

Fill in **every** variable below.  Never commit `.env.prod` to version control.

```bash
# ── Django ─────────────────────────────────────────────────────────────────────
SECRET_KEY=<generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DEBUG=False
ALLOWED_HOSTS=abem.yourdomain.com,www.abem.yourdomain.com
DJANGO_SETTINGS_MODULE=config.settings.production

# ── Database ───────────────────────────────────────────────────────────────────
POSTGRES_DB=abem_prod
POSTGRES_USER=abem_user
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_HOST=db               # service name in docker-compose.prod.yml
POSTGRES_PORT=5432

# ── Redis ──────────────────────────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── JWT ───────────────────────────────────────────────────────────────────────
# (uses Django SECRET_KEY by default — no extra var needed unless overriding)

# ── Cloudinary (media storage) ─────────────────────────────────────────────────
# Reference: https://cloudinary.com/documentation/django_integration
CLOUDINARY_CLOUD_NAME=<your-cloud-name>
CLOUDINARY_API_KEY=<your-api-key>
CLOUDINARY_API_SECRET=<your-api-secret>

# ── Celery / Email ─────────────────────────────────────────────────────────────
CELERY_BROKER_URL=redis://redis:6379/0
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<your-email@gmail.com>
EMAIL_HOST_PASSWORD=<gmail-app-password>   # https://support.google.com/accounts/answer/185833

# ── Firebase (push notifications) ─────────────────────────────────────────────
# Reference: https://firebase.google.com/docs/admin/setup
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# ── Sentry (error tracking — optional but recommended) ────────────────────────
# Reference: https://docs.sentry.io/platforms/python/guides/django/
SENTRY_DSN=<your-sentry-dsn>

# ── Frontend ──────────────────────────────────────────────────────────────────
VITE_API_BASE_URL=https://abem.yourdomain.com/api/v1
```

> **Security tip:** Use a secrets manager such as [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html), [HashiCorp Vault](https://developer.hashicorp.com/vault/docs), or [Doppler](https://docs.doppler.com/) to store and inject secrets at runtime.

---

## 6. Docker — Production Deployment

This is the **recommended** deployment method.

### 6.1 Build and Start All Services

```bash
cd /opt/abem

# Build images (first time or after code changes)
docker compose -f docker-compose.prod.yml build

# Start all services in detached mode
docker compose -f docker-compose.prod.yml up -d

# Verify all containers are running
docker compose -f docker-compose.prod.yml ps
```

Expected output:

```
NAME                    IMAGE         STATUS         PORTS
abem-backend-1          abem-backend  Up             8000/tcp
abem-celery_worker-1    abem-backend  Up
abem-celery_beat-1      abem-backend  Up
abem-db-1               postgres:16   Up (healthy)   5432/tcp
abem-redis-1            redis:7       Up (healthy)   6379/tcp
abem-frontend-1         abem-frontend Up             0.0.0.0:80->80/tcp
```

### 6.2 Run Migrations

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### 6.3 Collect Static Files

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

> Static files are served by [WhiteNoise](https://whitenoise.readthedocs.io/) directly from Gunicorn — no separate Nginx step needed for static files.

### 6.4 Update Without Downtime

```bash
cd /opt/abem
git pull origin main                                    # fetch latest code
docker compose -f docker-compose.prod.yml build backend  # rebuild backend image
docker compose -f docker-compose.prod.yml up -d --no-deps backend  # replace only backend
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

---

## 7. Manual (Non-Docker) Deployment

Use this if you prefer managing services directly on the host.

### 7.1 Python Environment

```bash
# Install Python 3.13
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update && sudo apt install -y python3.13 python3.13-venv python3.13-dev libpq-dev

cd /opt/abem/backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements/production.txt
```

### 7.2 Gunicorn Service (systemd)

```bash
sudo nano /etc/systemd/system/abem-gunicorn.service
```

Paste:

```ini
[Unit]
Description=ABEM Gunicorn daemon
Requires=abem-gunicorn.socket
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/abem/backend
EnvironmentFile=/opt/abem/.env.prod
ExecStart=/opt/abem/backend/.venv/bin/gunicorn \
          config.wsgi:application \
          --bind unix:/run/abem-gunicorn.sock \
          --workers 4 \
          --timeout 120
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo nano /etc/systemd/system/abem-gunicorn.socket
```

Paste:

```ini
[Unit]
Description=ABEM Gunicorn socket

[Socket]
ListenStream=/run/abem-gunicorn.sock

[Install]
WantedBy=sockets.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now abem-gunicorn.socket
sudo systemctl status abem-gunicorn
```

**Reference:** [Django + Gunicorn deployment guide](https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/gunicorn/)

---

## 8. Database Setup & Migrations

### 8.1 PostgreSQL (Manual, Non-Docker)

```bash
sudo apt install -y postgresql postgresql-contrib
sudo -u postgres psql

-- Inside psql:
CREATE DATABASE abem_prod;
CREATE USER abem_user WITH PASSWORD '<strong-password>';
GRANT ALL PRIVILEGES ON DATABASE abem_prod TO abem_user;
\q
```

**Reference:** [PostgreSQL installation guide (Ubuntu)](https://www.postgresql.org/download/linux/ubuntu/)

### 8.2 Run Migrations

```bash
# Docker
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Non-Docker
source /opt/abem/backend/.venv/bin/activate
cd /opt/abem/backend
python manage.py migrate
```

### 8.3 Database Backups

```bash
# Create a backup
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U abem_user abem_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U abem_user abem_prod < backup_20260226_120000.sql
```

**Reference:** [pg_dump documentation](https://www.postgresql.org/docs/16/app-pgdump.html)

---

## 9. Superuser Creation

The initial admin account must be created manually on first deployment.

### 9.1 Using Django `createsuperuser`

```bash
# Docker
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py createsuperuser

# Non-Docker
source /opt/abem/backend/.venv/bin/activate
python manage.py createsuperuser
```

When prompted, enter:

| Field    | Value               |
|----------|---------------------|
| Username | `shebo`             |
| Email    | `cegres1@yahoo.com` |
| Password | `A12@xval`         |

> **Important:** Change the password immediately after the first login via the Django Admin panel at `/admin/` or the profile API endpoint `PATCH /api/v1/auth/profile/change-password/`.

### 9.2 Non-interactive Superuser (CI/CD)

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py shell -c "
from apps.authentication.models import User
if not User.objects.filter(email='cegres1@yahoo.com').exists():
    User.objects.create_superuser(
        email='cegres1@yahoo.com',
        username='shebo',
        password='A12@xval',
        role='admin',
    )
    print('Superuser created.')
else:
    print('Superuser already exists.')
"
```

---

## 10. Static & Media Files

### Static Files (WhiteNoise)

WhiteNoise is configured and serves compressed static files directly from Gunicorn — no additional configuration needed.

```bash
# Collect static files
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py collectstatic --noinput
```

**Reference:** [WhiteNoise documentation](https://whitenoise.readthedocs.io/en/stable/django.html)

### Media Files (Cloudinary)

User-uploaded files (expense bills, profile photos) are stored on [Cloudinary](https://cloudinary.com/documentation/django_integration).  Ensure the three Cloudinary environment variables are set in `.env.prod`.

---

## 11. Nginx & TLS / HTTPS

### 11.1 Install Certbot (Let's Encrypt)

```bash
sudo apt install -y nginx certbot python3-certbot-nginx

# Obtain and install a free TLS certificate
sudo certbot --nginx -d abem.yourdomain.com -d www.abem.yourdomain.com

# Auto-renewal (runs daily via systemd timer — verify it works)
sudo certbot renew --dry-run
```

**Reference:** [Certbot documentation](https://certbot.eff.org/instructions?os=ubuntufocal&tab=standard)

### 11.2 Nginx Configuration (API + Frontend Reverse Proxy)

> Skip this step if using Docker — the production `docker-compose.prod.yml` embeds Nginx inside the `frontend` container.

```bash
sudo nano /etc/nginx/sites-available/abem
```

Paste the following (replace `abem.yourdomain.com`):

```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    server_name abem.yourdomain.com www.abem.yourdomain.com;
    return 301 https://$host$request_uri;
}

# HTTPS main server
server {
    listen 443 ssl http2;
    server_name abem.yourdomain.com www.abem.yourdomain.com;

    # TLS (managed by Certbot)
    ssl_certificate     /etc/letsencrypt/live/abem.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/abem.yourdomain.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # API proxy → Gunicorn
    location /api/ {
        proxy_pass         http://unix:/run/abem-gunicorn.sock;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        client_max_body_size 15M;
    }

    location /admin/ {
        proxy_pass         http://unix:/run/abem-gunicorn.sock;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    # React SPA — serve built files
    root /opt/abem/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1024;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/abem /etc/nginx/sites-enabled/
sudo nginx -t          # test config
sudo systemctl reload nginx
```

**Reference:** [Nginx beginners guide](https://nginx.org/en/docs/beginners_guide.html)

---

## 12. Celery (Background Tasks)

Celery processes email notifications, push notifications (FCM), and scheduled tasks.

### 12.1 Docker (Automatic)

The `celery_worker` and `celery_beat` services start automatically with `docker compose up`.

### 12.2 systemd Services (Non-Docker)

**Worker:**

```bash
sudo nano /etc/systemd/system/abem-celery-worker.service
```

```ini
[Unit]
Description=ABEM Celery Worker
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/abem/backend
EnvironmentFile=/opt/abem/.env.prod
ExecStart=/opt/abem/backend/.venv/bin/celery \
          -A config worker -l warning --concurrency 4
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**Beat (scheduler):**

```bash
sudo nano /etc/systemd/system/abem-celery-beat.service
```

```ini
[Unit]
Description=ABEM Celery Beat Scheduler
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/abem/backend
EnvironmentFile=/opt/abem/.env.prod
ExecStart=/opt/abem/backend/.venv/bin/celery \
          -A config beat -l warning
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now abem-celery-worker abem-celery-beat
```

**Reference:** [Celery daemonization guide](https://docs.celeryq.dev/en/stable/userguide/daemonizing.html)

---

## 13. Frontend Build & Deployment

### 13.1 Docker (Automatic)

The `frontend` container in `docker-compose.prod.yml` builds and serves the React app via Nginx automatically.

### 13.2 Manual Build

```bash
cd /opt/abem/frontend

# Set the production API URL
echo "VITE_API_BASE_URL=https://abem.yourdomain.com/api/v1" > .env.production

# Install dependencies and build
npm ci
npm run build

# The built files are in /opt/abem/frontend/dist/
# Point your Nginx root to this directory (see Step 10)
```

**Reference:** [Vite environment variables guide](https://vitejs.dev/guide/env-and-mode.html)

---

## 14. Mobile (Flutter) Release

### 14.1 Android (Google Play Store)

1. **Set up signing key:**

   ```bash
   # Generate a keystore (one-time)
   keytool -genkey -v -keystore ~/abem-release.keystore \
     -alias abem -keyalg RSA -keysize 2048 -validity 10000
   ```

2. **Configure signing in `android/app/build.gradle`:**

   ```groovy
   android {
       signingConfigs {
           release {
               storeFile file(System.getenv("KEYSTORE_PATH") ?: "../abem-release.keystore")
               storePassword System.getenv("KEYSTORE_PASS")
               keyAlias "abem"
               keyPassword System.getenv("KEY_PASS")
           }
       }
       buildTypes {
           release { signingConfig signingConfigs.release }
       }
   }
   ```

3. **Build the release APK / App Bundle:**

   ```bash
   cd /opt/abem/mobile
   flutter build appbundle --release   # recommended for Play Store
   flutter build apk --release         # direct APK install
   ```

4. **Upload to Google Play Console:**
   - Go to [Google Play Console](https://play.google.com/console)
   - Create a new app → Upload the `.aab` file from `build/app/outputs/bundle/release/`

   **Reference:** [Flutter Android release guide](https://docs.flutter.dev/deployment/android)

### 14.2 iOS (Apple App Store)

1. **Requirements:** macOS machine, Xcode 15+, Apple Developer account ($99/year)
2. **Archive and distribute:**

   ```bash
   cd /opt/abem/mobile
   flutter build ios --release
   # Open Xcode → Product → Archive → Distribute App → App Store Connect
   ```

   **Reference:** [Flutter iOS release guide](https://docs.flutter.dev/deployment/ios)

---

## 15. CI/CD — GitHub Actions

Three workflows are already configured in `.github/workflows/`:

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `backend-ci.yml` | Push/PR to `main`/`develop` | flake8 · black · pytest (≥70% coverage) · Docker build |
| `frontend-ci.yml` | Push/PR to `main`/`develop` | ESLint · Vite production build |
| `mobile-ci.yml` | Push/PR to `main`/`develop` | dart analyze · flutter test |

### Adding Automated Deployment (CD)

Append a deployment job to `backend-ci.yml` (after tests pass):

```yaml
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/abem
            git pull origin main
            docker compose -f docker-compose.prod.yml build backend
            docker compose -f docker-compose.prod.yml up -d --no-deps backend
            docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate
```

**Required GitHub Secrets:** `PROD_HOST`, `PROD_USER`, `PROD_SSH_KEY`

**Reference:**
- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [appleboy/ssh-action](https://github.com/appleboy/ssh-action)

---

## 16. Monitoring & Logging

### Application Error Tracking (Sentry)

1. Create a project at [sentry.io](https://sentry.io/welcome/)
2. Copy the DSN and add to `.env.prod`:

   ```bash
   SENTRY_DSN=https://<key>@o<org>.ingest.sentry.io/<project>
   ```

Sentry is already integrated in `config/settings/production.py`.

**Reference:** [Sentry Django integration](https://docs.sentry.io/platforms/python/guides/django/)

### Container Logs

```bash
# Stream all service logs
docker compose -f docker-compose.prod.yml logs -f

# Stream only backend logs
docker compose -f docker-compose.prod.yml logs -f backend

# Tail last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

### System Resource Monitoring

```bash
# Install htop
sudo apt install -y htop
htop

# Docker stats
docker stats
```

---

## 17. Post-Deployment Smoke Tests

Run the Sprint 10 smoke suite immediately after every deployment:

```bash
cd /opt/abem/abem-automation
source .venv/bin/activate

# Point at production
export TEST_ENV=production          # or set in environments.yaml

# Run all 15 smoke tests (should complete in < 60 seconds)
pytest -m smoke --tb=short -q

# Expected output:
# 15 passed in Xs
```

### Manual Verification Checklist

| # | Check | Command / URL |
|---|-------|---------------|
| 1 | Health endpoint | `curl https://abem.yourdomain.com/api/health/` |
| 2 | Swagger UI | Open `https://abem.yourdomain.com/api/docs/` in browser |
| 3 | Admin panel | Open `https://abem.yourdomain.com/admin/` — log in with credentials below |
| 4 | Web frontend | Open `https://abem.yourdomain.com/` — log in as admin |
| 5 | TLS certificate | `curl -I https://abem.yourdomain.com/` → check `Strict-Transport-Security` header |

---

## 18. Rollback Procedure

### Docker Rollback

```bash
cd /opt/abem

# Revert to the previous Git commit
git log --oneline -5              # find the target commit hash
git checkout <previous-commit>

# Rebuild and restart
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d --no-deps backend

# If migration rollback is needed (destructive — verify first)
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py migrate <app_name> <previous_migration>
```

### Database Point-in-Time Restore

```bash
# Stop services
docker compose -f docker-compose.prod.yml stop backend celery_worker

# Restore from backup
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U abem_user abem_prod < backup_YYYYMMDD_HHMMSS.sql

# Restart
docker compose -f docker-compose.prod.yml start backend celery_worker
```

---

## 19. Security Hardening Checklist

- [ ] `DEBUG=False` in production settings
- [ ] `SECRET_KEY` is a random 50-character string (not the dev default)
- [ ] `ALLOWED_HOSTS` only contains your domain(s)
- [ ] HTTPS enforced (`SECURE_SSL_REDIRECT=True`, HSTS headers set)
- [ ] Database password is strong and unique
- [ ] `.env.prod` has `chmod 600 .env.prod` (readable only by owner)
- [ ] Superuser password changed from the default after first login
- [ ] `DJANGO_SUPERUSER_PASSWORD` not stored in source control
- [ ] Sentry DSN configured for error monitoring
- [ ] Cloudinary credentials are restricted to the ABEM application
- [ ] Firebase credentials file is not committed to version control
- [ ] Server firewall allows only ports 22, 80, 443
- [ ] Automatic security updates enabled: `sudo apt install unattended-upgrades`
- [ ] TLS certificate auto-renewal tested: `sudo certbot renew --dry-run`
- [ ] PostgreSQL not exposed on 0.0.0.0 (only accessible from `localhost`/Docker network)

---

## 20. Useful References

| Topic | Link |
|-------|------|
| Django deployment checklist | https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/ |
| Django + Gunicorn | https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/gunicorn/ |
| DRF documentation | https://www.django-rest-framework.org/ |
| drf-spectacular (OpenAPI) | https://drf-spectacular.readthedocs.io/en/latest/ |
| SimpleJWT | https://django-rest-framework-simplejwt.readthedocs.io/en/latest/ |
| Docker Compose reference | https://docs.docker.com/compose/compose-file/ |
| PostgreSQL 16 docs | https://www.postgresql.org/docs/16/ |
| Redis documentation | https://redis.io/docs/ |
| Celery documentation | https://docs.celeryq.dev/en/stable/ |
| WhiteNoise | https://whitenoise.readthedocs.io/en/stable/ |
| Certbot (Let's Encrypt) | https://certbot.eff.org/ |
| Nginx documentation | https://nginx.org/en/docs/ |
| Flutter Android release | https://docs.flutter.dev/deployment/android |
| Flutter iOS release | https://docs.flutter.dev/deployment/ios |
| GitHub Actions | https://docs.github.com/en/actions |
| Sentry Django | https://docs.sentry.io/platforms/python/guides/django/ |
| Cloudinary Django | https://cloudinary.com/documentation/django_integration |
| OWASP Top 10 | https://owasp.org/www-project-top-ten/ |

---

*Last updated: 2026-02-26 — Sprint 10 (Deployment & Launch)*
