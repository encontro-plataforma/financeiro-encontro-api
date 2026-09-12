FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

COPY . .

ENV APP_PORT=8000
ENV UPLOAD_FOLDER=/app/uploads

EXPOSE 8000

CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT}"]
