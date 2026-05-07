FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=autoservice.settings.prod

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

COPY . .

RUN mkdir -p /app/staticfiles /app/media && \
    python manage.py collectstatic --noinput || true

RUN adduser --disabled-password --no-create-home appuser && \
    chown -R appuser:appuser /app/staticfiles /app/media
USER appuser

EXPOSE 8000

CMD ["gunicorn", "autoservice.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
