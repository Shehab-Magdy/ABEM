# Deploy ABEM Backend to Render.com

This document explains how to deploy the `backend` Django app to Render using a Render blueprint and managed dependencies.

## What changed

- Added `render.yaml` at the repository root.
- Updated `backend/config/settings/production.py` for Render proxy support and safer database URL fallback.
- The backend uses the existing `backend/Dockerfile` and `backend/requirements.txt`.

## Architecture on Render

The Render deployment includes:

- `abem-backend` — web service for Django
- `abem-celery-worker` — background Celery worker
- `abem-redis` — managed Redis instance
- **External PostgreSQL** — Neon database (not managed by Render)

## Required external dependencies

The backend uses the following external dependencies:

- PostgreSQL database
- Redis cache / Celery broker
- Cloudinary storage for uploaded media files
- Optional: Sentry, email SMTP provider

## Step-by-step deployment

### 1. Connect your Git repository to Render

1. Sign in to Render and connect your GitHub/GitLab account.
2. Link the repository containing the `ABEM` project.
3. Ensure that Render can see the root repository and the `backend` folder.

### 2. Confirm the Render blueprint file

Render will use `render.yaml` at the repository root to define services.

The blueprint defines:

- `abem-backend` (web)
- `abem-celery-worker` (worker)
- `abem-redis` (Redis service)

The **PostgreSQL database** is managed externally at Neon (not in the blueprint).

### 3. Set environment variables

In Render, add the following environment variables for both the web service and the worker service.

#### Required variables

- `DJANGO_SETTINGS_MODULE = config.settings.production`
- `DJANGO_DEBUG = False`
- `DJANGO_SECRET_KEY` = a secure secret string (generate a new one)
- `DATABASE_URL = postgresql://neondb_owner:npg_LC8SMVOfyKu5@ep-polished-mud-alglb0gn.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require`
- `CLOUDINARY_CLOUD_NAME = dudq2w3yz`
- `CLOUDINARY_API_KEY = 265124733791196`
- `CLOUDINARY_API_SECRET = 8-O5exUQ0CtWxKm6oRCuES9i5o8`

#### Optional / recommended variables

- `SENTRY_DSN` if you want error reporting
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`
- `CORS_ALLOWED_ORIGINS` to allow frontend domains (e.g., `https://frontend.onrender.com`)

### 4. Bind managed services

Render should automatically bind `REDIS_URL` from the `abem-redis` service in the blueprint.

The `DATABASE_URL` is already set manually in step 3 and points to your Neon PostgreSQL instance.

### 5. Deploy the web service

Render will build the `backend` service using `backend/Dockerfile`.

The Dockerfile already:

- installs dependencies from `requirements/production.txt`
- copies the backend source
- runs `python manage.py collectstatic --noinput`
- starts `gunicorn config.wsgi:application`

### 6. Deploy the Celery worker

The worker service runs:

```bash
celery -A config worker --loglevel=info
```

This ensures background tasks work correctly if the project uses Celery.

### 7. Run database migrations

After the service is deployed, run migrations in Render:

```bash
python manage.py migrate
```

You can do this using Render's dashboard terminal or a one-off shell command.

### 8. Verify deployment

- Browse the Render web service URL.
- Check the logs for `gunicorn` startup and `collectstatic` completion.
- Ensure the application can connect to Postgres and Redis.
- Confirm uploaded media works using Cloudinary credentials.

## Special deployment notes

### Cloudinary media

The backend stores uploaded media on Cloudinary using:

- `CLOUDINARY_CLOUD_NAME = dudq2w3yz`
- `CLOUDINARY_API_KEY = 265124733791196`
- `CLOUDINARY_API_SECRET = 8-O5exUQ0CtWxKm6oRCuES9i5o8`

These are already configured. Media upload will work automatically.

### Database connection (Neon PostgreSQL)

The database URL is configured to connect to Neon:

`postgresql://neondb_owner:npg_LC8SMVOfyKu5@ep-polished-mud-alglb0gn.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require`

This is an external managed database, so Render will not manage it. SSL is required for the connection.

### Render proxy support

`backend/config/settings/production.py` now includes:

- `SECURE_PROXY_SSL_HEADER`
- `USE_X_FORWARDED_HOST`
- `CSRF_TRUSTED_ORIGINS`

This is required for Render's HTTPS proxy.

## Local testing before deploy

1. Create a `.env` file with the same required variables.
2. Run locally with `DJANGO_SETTINGS_MODULE=config.settings.production`.
3. Execute `python manage.py migrate` and `python manage.py runserver 0.0.0.0:8000`.

## Useful commands

- `python manage.py migrate`
- `python manage.py collectstatic --noinput`
- `python manage.py createsuperuser`
- `celery -A config worker --loglevel=info`

## Troubleshooting

If the web service fails to start:

- Confirm `DJANGO_SECRET_KEY` is set and unique.
- Confirm `DATABASE_URL` is set to your Neon connection string and accessible.
- Confirm `REDIS_URL` is bound from the `abem-redis` service.
- Confirm `CLOUDINARY_*` variables are set correctly (already provided).
- Confirm `DJANGO_SETTINGS_MODULE` is `config.settings.production`.
