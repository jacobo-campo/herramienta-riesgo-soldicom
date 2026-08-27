# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

ARG APP_UID=10001
ARG APP_GID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1

WORKDIR /app

RUN groupadd --gid "${APP_GID}" app \
    && useradd --uid "${APP_UID}" --gid app --home-dir /app --no-create-home --no-log-init --shell /usr/sbin/nologin app \
    && install -d -o app -g app -m 0750 /app/data

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY --chown=app:app . .

USER app

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"]

CMD ["/bin/sh", "-ec", "/app/.venv/bin/python -m history_storage check && exec /app/.venv/bin/streamlit run app.py --server.headless=true --server.address=0.0.0.0 --server.port=8501"]
