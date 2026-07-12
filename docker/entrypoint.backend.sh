#!/bin/sh
set -e

echo "Aguardando PostgreSQL..."
until python - <<'PY'
import os
import sys
import psycopg2

conn = psycopg2.connect(
    host=os.environ.get("POSTGRES_HOST", "postgres-app"),
    port=os.environ.get("POSTGRES_PORT", "5432"),
    dbname=os.environ.get("POSTGRES_DB", "moneyconnect"),
    user=os.environ.get("POSTGRES_USER", "moneyconnect"),
    password=os.environ.get("POSTGRES_PASSWORD", "moneyconnect_pass"),
)
conn.close()
PY
do
  sleep 2
done

echo "Aplicando migrações..."
python manage.py migrate --noinput

echo "Garantindo usuário admin..."
python manage.py create_admin

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

exec "$@"
