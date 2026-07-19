# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**financeiro-encontro-api** is the backend of the Financeiro Encontro platform — a financial management system for church events. It handles income/expense tracking, payment reconciliation via CSV import (Banco Inter), dashboard reporting, and JWT-based authentication.

This repository was extracted from the former `financeiro-encontro` monorepo (2026-07-19) and now lives alongside two sibling repositories under the `encontro-plataforma` GitHub org:

- [`financeiro-encontro-web`](https://github.com/encontro-plataforma/financeiro-encontro-web) — Angular frontend
- [`infra-encontro`](https://github.com/encontro-plataforma/infra-encontro) — local Docker Compose infra (db, and full-stack orchestration)

For local full-stack development, clone all three repos as sibling folders (see `infra-encontro`'s README).

## Development Commands

### Database (start first)
Use the sibling `infra-encontro` repo:
```bash
docker compose -f ../infra-encontro/docker-compose-db.yml up -d
# PostgreSQL on :5432, pgAdmin on :9090
```

### Backend (FastAPI/Python)
```bash
cp .env.example .env   # first time only — fill in values
./start-backend.sh     # creates venv, installs deps, loads .env, runs uvicorn on $APP_PORT
```

## Architecture

### Stack
- Python 3.11 + FastAPI + SQLAlchemy 2.0 + PostgreSQL 15

### Layer Structure (`app/`)
```
core/         # config.py (all env vars), security.py (JWT + bcrypt), exceptions, deps.py (get_current_user)
database/     # DB session factory, seed data loader (runs on startup via lifespan)
models/       # SQLAlchemy ORM models + enums
schemas/      # Pydantic request/response schemas + filter DTOs
repositories/ # Data access layer — all DB queries live here
services/     # Business logic — orchestrates repositories
routers/      # FastAPI route handlers — thin, delegate to services
integracao/   # CSV parsing (ParserFactory pattern) + Conciliador engine
utils/        # Shared helpers (hash_utils, sort_utils)
```

**Key domain models:**
- `Lancamento`: Financial transaction (RECEITA/DESPESA), with payment form (PIX/DINHEIRO/CARTAO_*), status (CONCILIADO/NAO_CONCILIADO), and a deduplication `hash_transacao`
- `Finalidade`: Category/purpose for a transaction — full CRUD via API; seeds provide initial data at startup
- `ExtratoBancario`: Imported bank statement file record
- `Usuario`: Authenticated user with `perfil` (ADMINISTRADOR/CONCILIADOR/REPORTER) — read-only via API, managed via seeds

### Authentication
All routes except `POST /auth/login` and `GET /health` require a JWT bearer token.
Token obtained via `POST /auth/login`. Dependency `get_current_user` in `core/deps.py` validates it on every protected request.
Users are seeded at startup — no registration endpoint.

### Deduplication Logic
Hashes are generated from `descricao_normalizada + valor + data_pagamento` (SHA-256). A unique constraint on `hash_transacao` in the DB prevents duplicates. The service layer checks before insert and the reconciliation engine (`Conciliador`) uses the same logic when processing CSV imports.

### CSV Reconciliation Flow
`POST /conciliacao/upload` → `ConciliacaoService` → `ParserFactory` (selects bank parser) → `Conciliador.processar()` → returns report with inserted/duplicated/errored counts. Currently only Banco Inter CSV format is supported.
After import, records are `NAO_CONCILIADO`. Manual reconciliation via `PATCH /lancamentos/conciliar-lancamento/{id}?idFinalidade={id}`.

### Dashboard Endpoints
`GET /dashboard/totais` — aggregated totals (receitas, despesas, saldo, quantidade).
`GET /dashboard/por-dia` — day-by-day breakdown for a period.
`GET /dashboard/por-mes` — month-by-month breakdown for a period.
`GET /dashboard/por-finalidade` — totals grouped by finalidade (id, nome, total_valor, quantidade).
All share the same filter DTO: `data_inicio`, `data_fim` (defaults: today → today+30d), `forma_pagamento[]`, `finalidade_id[]`, `tipo`, `status`.

## Key Config Locations
- **All env vars**: `app/core/config.py` — single source of truth, reads from environment
- **Local dev env**: `.env` (gitignored) — copy from `.env.example`
- **Python deps**: `requirements.txt`
- **DB schema**: managed via Alembic migrations (`alembic/versions/`)
- **Seed data**: `app/database/seeds/` — runs on startup, idempotent
- **Deploy**: `render.yaml` (Render Blueprint — web service, runs `alembic upgrade head` on build)

## Environment Variables Reference

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://...@localhost:5432/financeiro_encontro` | DB connection string |
| `UPLOAD_FOLDER` | `uploads` | Folder for uploaded CSV files |
| `APP_PORT` | `8000` | Port uvicorn listens on |
| `APP_VERSION` | `0.0.1` | App version, shown in `/health` |
| `JWT_SECRET` | `changeme-insecure-secret` | JWT signing key — always override in production |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_EXPIRE_MINUTES` | `480` | Token expiry (8 hours) |
| `SQL_ECHO` | `false` | Log all SQL queries to console — enable in development only |
| `CORS_ORIGINS` | `http://localhost:4200` | Allowed CORS origins (comma-separated) — set to the `financeiro-encontro-web` deployed URL in production |
