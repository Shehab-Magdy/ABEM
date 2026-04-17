# Deploy ABEM Backend to Fly.io (Free Tier)

**Note**: This guide has been updated to use **Fly.io** instead of Render because:
- Fly.io's free tier doesn't spin down (better for production)
- Supports background Celery workers
- 3 shared VMs available for free
- No uptime restrictions

All services use **free tiers** only (Fly.io, Neon, Redis Cloud, Cloudinary).

## System Requirements

Before starting, ensure you have:

1. **Fly.io account** (https://fly.io) — free
2. **Flyctl CLI** installed — download from https://fly.io/docs/getting-started/installing-flyctl/
3. **Git** and **Docker** (usually already installed)
4. **A GitHub/GitLab repository** with this code

## Free tier limits (Fly.io)

| Service | Free Tier Limit |
|---------|-----------------|
| Compute | 3 × shared CPU 256 MB RAM (shared-cpu-1x) |
| Egress | 160 GB/month |
| Databases | None included (external only) |
| Apps | Unlimited |

## Free external services (Required)

All external services use their free tier:

| Service | Free Tier | Purpose |
|---------|-----------|---------|
| **Neon PostgreSQL** | 512 MB storage | Database |
| **Redis Cloud** | 30 MB storage | Celery broker/cache |
| **Cloudinary** | 25 GB storage | Media storage |

This guide walks through this configuration step-by-step.

## Architecture on Fly.io

The Fly.io deployment includes:

- `abem-backend` (web process) — Django/Gunicorn server
- `abem-celery-worker` (worker process) — Background task processor
- **External PostgreSQL** — Neon database (free tier)
- **External Redis** — Redis Cloud (free tier)
- **External media storage** — Cloudinary (free tier)

Both processes run on the same Fly.io machine in the free tier.

## Step-by-step deployment

### Prerequisites

1. **Fly.io account**: Create a free account at https://fly.io
2. **Fly CLI installed**: Install from https://fly.io/docs/getting-started/installing-flyctl/
3. **Git and Docker**: Already installed on your system
4. **External service credentials** (all free tier):
   - Neon PostgreSQL connection string
   - Redis Cloud connection string
   - Cloudinary credentials

### Step 1: Create a Fly.io app

1. Log in to Fly.io:

```bash
flyctl auth login
```

2. Navigate to your project root:

```bash
cd /path/to/ABEM
```

3. Launch a new Fly.io app:

```bash
flyctl launch
```

4. When prompted:
   - **App name**: Enter `abem-backend` (or your preferred name)
   - **Region**: Choose one close to you (e.g., `iad` for US East, `lhr` for London)
   - **Copy configuration to fly.toml**: Say `yes`
   - **Would you like to set up a PostgreSQL?**: Say `no` (we'll use external Neon)
   - **Redis**: Say `no` (we'll use external Redis Cloud)

This creates `fly.toml` in your repository root.

### Step 2: Update `fly.toml` for Django and Celery

Edit the generated `fly.toml` and update it to match this structure:

```toml
app = "abem-backend"
primary_region = "iad"

[build]
  dockerfile = "backend/Dockerfile"

[env]
  DJANGO_SETTINGS_MODULE = "config.settings.production"
  DJANGO_DEBUG = "False"
  PORT = "8000"

[processes]
  web = "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120"
  worker = "celery -A config worker --loglevel=info"

[[services]]
  protocol = "tcp"
  internal_port = 8000

  [services.concurrency]
    type = "connections"
    hard_limit = 25
    soft_limit = 20

  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [services.http_checks]
    enabled = true
    grace_period = "10s"
    interval = "30s"
    timeout = "5s"
    method = "GET"
    path = "/api/v1/"

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

### Step 3: Set environment variables

Set the required environment variables for your Fly.io app:

```bash
flyctl secrets set \
  DJANGO_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')" \
  DATABASE_URL="postgresql://neondb_owner:npg_LC8SMVOfyKu5@ep-polished-mud-alglb0gn.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require" \
  REDIS_URL="redis://default:password@redis-cloud-host:port" \
  CLOUDINARY_CLOUD_NAME="dudq2w3yz" \
  CLOUDINARY_API_KEY="265124733791196" \
  CLOUDINARY_API_SECRET="8-O5exUQ0CtWxKm6oRCuES9i5o8" \
  CORS_ALLOWED_ORIGINS="https://your-frontend.onrender.com"
```

**Replace these values**:
- `DJANGO_SECRET_KEY`: Generate a new one (the command does this automatically)
- `DATABASE_URL`: Your Neon PostgreSQL connection string
- `REDIS_URL`: Your Redis Cloud connection string (format: `redis://default:password@host:port`)

### Step 4: Deploy the web service

Deploy your app to Fly.io:

```bash
flyctl deploy
```

This will:
1. Build the Docker image from `backend/Dockerfile`
2. Push it to Fly.io registry
3. Deploy the web process
4. Start the worker process (in the same machine)

Wait for the deployment to complete. You'll see a message with your app URL (e.g., `https://abem-backend.fly.dev`).

### Step 5: Run database migrations

Once the app is deployed, run migrations:

```bash
flyctl ssh console
```

This opens an SSH console on the running container. Run:

```bash
python manage.py migrate
```

Create a superuser:

```bash
python manage.py createsuperuser
```

Collect static files:

```bash
python manage.py collectstatic --noinput
```

Type `exit` to close the SSH console.

### Step 6: Verify deployment

1. **Visit your app**: Open https://abem-backend.fly.dev (or your app's URL)
2. **Check API**: Navigate to `https://abem-backend.fly.dev/api/v1/`
3. **View logs**:

```bash
flyctl logs
```

4. **Check status**:

```bash
flyctl status
```

5. **Verify worker is running**:

```bash
flyctl ssh console
celery -A config inspect active
```

### Step 7: Configure Redis Cloud (if not done yet)

If you haven't set up Redis Cloud:

1. Go to https://redis.com/cloud
2. Sign up for free tier (30 MB storage)
3. Create a database in a region near your Fly.io region
4. Copy the connection string (format: `redis://default:password@host:port`)
5. Update Fly.io secrets:

```bash
flyctl secrets set REDIS_URL="your-redis-cloud-url"
```

6. Redeploy:

```bash
flyctl deploy
```

## External Services Setup (All Free Tier)

### Neon PostgreSQL (Free Tier)

1. Go to https://neon.tech
2. Sign up (free account)
3. Create a new project
4. Copy the connection string (format: `postgresql://user:password@host:5432/database?sslmode=require`)
5. Use this as `DATABASE_URL` in Fly.io secrets

**Free tier limits**: 512 MB storage, 1 GB/month egress

### Redis Cloud (Free Tier)

1. Go to https://redis.com/cloud
2. Sign up (free account)
3. Create a free database (30 MB)
4. Copy the connection string (format: `redis://default:password@host:port`)
5. Use this as `REDIS_URL` in Fly.io secrets

**Free tier limits**: 30 MB storage, 30 concurrent connections

### Cloudinary (Free Tier)

Already configured with your credentials:
- Cloud name: `dudq2w3yz`
- API key: `265124733791196`
- API secret: `8-O5exUQ0CtWxKm6oRCuES9i5o8`

**Free tier limits**: 25 GB storage, 5 GB/month bandwidth

## Useful Fly.io commands

```bash
# View live logs
flyctl logs

# SSH into your app
flyctl ssh console

# Check app status
flyctl status

# List all VMs
flyctl machines list

# Scale to multiple instances
flyctl scale count=2

# View metrics
flyctl metrics

# Update environment variable
flyctl secrets set VARIABLE_NAME="new_value"

# Deploy latest code
flyctl deploy

# Rollback to previous version
flyctl releases
flyctl releases rollback

# View environment variables (secrets are hidden)
flyctl config show
```

## After deployment

### Redeploy after code changes

1. Commit and push to main branch:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

2. Deploy to Fly.io:

```bash
flyctl deploy
```

Alternatively, set up GitHub Actions for automatic deployment.

### Monitor your app

View real-time logs:

```bash
flyctl logs -n 100  # last 100 lines
flyctl logs --follow  # live tail
```

Check metrics:

```bash
flyctl metrics
```

### Troubleshoot Celery tasks

SSH into the app and run:

```bash
flyctl ssh console
celery -A config inspect active
celery -A config inspect registered
```

### Scale the app

To use multiple instances:

```bash
flyctl scale count=2
```

Note: On Fly.io's free tier, you're limited to one shared instance. To scale beyond the free tier, you'll need a paid plan.

### Update secrets

If you need to update any environment variables:

```bash
flyctl secrets set VARIABLE_NAME="new_value"
```

Fly.io will automatically redeploy with the new secrets.

### Destroy the app

If you want to stop and remove your app:

```bash
flyctl apps destroy abem-backend
```

## Troubleshooting

### Web service fails to start

1. **Check logs**:

```bash
flyctl logs
```

2. **Common issues**:
   - Missing `DJANGO_SECRET_KEY` or `DATABASE_URL`
   - Database not accessible from Fly.io
   - Port configuration issue

3. **SSH into app to debug**:

```bash
flyctl ssh console
python manage.py check
python manage.py migrate --plan
```

### Celery worker not running

1. **Check process status**:

```bash
flyctl ssh console
ps aux | grep celery
```

2. **Check Redis connection**:

```bash
flyctl ssh console
python manage.py shell
import redis
redis.from_url(os.environ['REDIS_URL']).ping()
```

3. **Restart the app**:

```bash
flyctl restart
```

### Database connection timeout

1. Verify Neon database is not paused
2. Check Neon firewall allows Fly.io region
3. Test locally with the same `DATABASE_URL`:

```bash
DATABASE_URL="your-url" python manage.py migrate
```

### Out of memory

Free tier instances have 256 MB RAM. If you run out:
1. Optimize Django settings (reduce worker count)
2. Upgrade to a paid plan with more RAM

### Redis connection refused

1. Verify `REDIS_URL` is correct
2. Check Redis Cloud account limits
3. Try: `flyctl secrets set REDIS_URL="correct-url"` and redeploy

### Files missing after deploy

Fly.io instances are ephemeral. Uploaded files should use Cloudinary (already configured). Check logs for Cloudinary upload errors.
