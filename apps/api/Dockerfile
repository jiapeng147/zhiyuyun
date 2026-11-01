# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e
FROM python:3.15-slim-bookworm@sha256:4e03260adeeebafccd084f3584e6b84823aba5651cfb53ef8a078ed441ddf9cd AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
WORKDIR /build
COPY requirements.txt ./
RUN pip install \
    --index-url https://pypi.org/simple \
    --require-hashes \
    --requirement requirements.txt

FROM python:3.15-slim-bookworm@sha256:4e03260adeeebafccd084f3584e6b84823aba5651cfb53ef8a078ed441ddf9cd

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --chown=app:app . .
RUN mkdir -p /app/uploads /app/data \
    && chown -R app:app /app/uploads /app/data

USER app
EXPOSE 12401
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "12401", "--no-proxy-headers", "--no-server-header", "--limit-concurrency", "200", "--timeout-keep-alive", "5"]
