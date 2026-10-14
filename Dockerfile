# syntax=docker/dockerfile:1
FROM python:3.12-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
COPY api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY api /app/api
RUN useradd --system --uid 10001 --home-dir /nonexistent cbuser
USER 10001
EXPOSE 8204
CMD ["uvicorn","api.main:app","--host","0.0.0.0","--port","8204","--proxy-headers","--forwarded-allow-ips","127.0.0.1"]

FROM nginx:1.27-alpine AS web
COPY deploy/docker/web-nginx.conf /etc/nginx/conf.d/default.conf
COPY web /usr/share/nginx/html
EXPOSE 8080
