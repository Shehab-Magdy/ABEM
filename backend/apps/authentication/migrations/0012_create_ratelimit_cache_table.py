# Generated manually (no model backs this table - see createcachetable docs)
"""
Provisions the DB table backing CACHES["ratelimit"]
(django.core.cache.backends.db.DatabaseCache), so `python manage.py migrate`
alone is enough to make the DB-backed rate-limit cache work - no separate
`createcachetable` step for engineers to remember.

SQL mirrors `python manage.py createcachetable ratelimit_cache_table --dry-run`
exactly (Django's DatabaseCache has no model, so this can't be a normal
CreateModel operation).
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0011_unusable_passwords"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'CREATE TABLE "ratelimit_cache_table" (\n'
                '    "cache_key" varchar(255) NOT NULL PRIMARY KEY,\n'
                '    "value" text NOT NULL,\n'
                '    "expires" timestamp with time zone NOT NULL\n'
                ");\n"
                'CREATE INDEX "ratelimit_cache_table_expires" '
                'ON "ratelimit_cache_table" ("expires");'
            ),
            reverse_sql='DROP TABLE IF EXISTS "ratelimit_cache_table";',
        ),
    ]
