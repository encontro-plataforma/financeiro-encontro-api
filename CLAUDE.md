# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**financeiro-encontro-api** is the backend of the Financeiro Encontro platform — a management system for church "Encontro" events. It has grown from pure financial tracking into two connected domains:

- **Financeiro**: income/expense tracking (`Lancamento`), bank statement reconciliation via CSV import (Banco Inter), dashboards, and PDF reports.
- **Secretaria**: registration management for **Encontreiros** (team members) and **Encontristas** (participants), grouped into **Equipes**/**Círculos**, also bulk-imported via CSV.

The bridge between the two is **Detalhamento** (a line-item breakdown of what a `Lancamento` actually pays for) and **Auditoria** (a background matching pass that automatically links pending Encontreiro/Encontrista payments to the right bank `Lancamento`, driven by a configurable **motor de regras** — see "Detalhamento & Auditoria" below).

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

On startup (`app/main.py` lifespan handler) the app auto-runs `alembic upgrade head` and loads/refreshes seed data — no manual migration step needed for local dev.

## Architecture

### Stack

- Python 3.11 + FastAPI + SQLAlchemy 2.0 + PostgreSQL 15 + Alembic

### Layer Structure (`app/`)

```text
core/         # config.py (all env vars), security.py (JWT + bcrypt), exceptions, deps.py (get_current_user)
database/     # DB session factory, seed data loader (runs on startup via lifespan)
models/       # SQLAlchemy ORM models + enums
schemas/      # Pydantic request/response schemas + filter DTOs
repositories/ # Data access layer — all DB queries live here
services/     # Business logic — orchestrates repositories
routers/      # FastAPI route handlers — thin, delegate to services
integracao/   # CSV parsing (ParserFactory pattern) + Conciliador engine (bank statements)
utils/        # Shared helpers (hash_utils, sort_utils)
```

### Routers (all mounted under `Depends(get_current_user)` except `/auth`)

| Prefix           | File                    | Purpose                                                                                          |
| ----------------- | ------------------------ | -------------------------------------------------------------------------------------------------- |
| `/auth`          | `auth_router.py`        | `POST /login`, `GET /me` — JWT login, current user (public).                                    |
| `/lancamentos`   | `lancamento_router.py`  | CRUD on `Lancamento` + `PATCH /conciliar/{id}/finalidade/{fid}`.                                |
| `/finalidades`   | `finalidade_router.py`  | CRUD on `Finalidade`.                                                                             |
| `/conciliacao`   | `conciliacao_router.py` | `POST /upload` — bank-statement CSV import (background-processed).                              |
| `/uploads`       | `upload_file_router.py` | List/get/download/delete uploaded files + `GET /{id}/status` (lightweight polling, no `conteudo_csv`). |
| `/dashboard`     | `dashboard_router.py`   | `GET /totais`, `/por-dia`, `/por-mes`, `/por-finalidade`.                                        |
| `/relatorios`    | `relatorio_router.py`   | `GET /livro-caixa`, `/resumo-geral` — PDF reports for a date range.                              |
| `/usuarios`      | `usuario_router.py`     | CRUD on `Usuario`.                                                                                 |
| `/equipes`       | `equipe_router.py`      | CRUD on `Equipe` (Encontreiro teams).                                                              |
| `/circulos`      | `circulo_router.py`     | CRUD on `Circulo` (Encontrista small-groups).                                                      |
| `/encontreiros`  | `encontreiro_router.py` | CRUD on `Encontreiro` + `POST /conciliacao` (CSV import, background-processed).                  |
| `/encontristas`  | `encontrista_router.py` | CRUD on `Encontrista` + `GET /padrinhos-disponiveis` + `PATCH /{id}/circulo/{circulo_id}` (changes only the círculo; id `0` clears it) + `POST /conciliacao` (CSV import). |
| `/detalhamentos` | `detalhamento_router.py`| CRUD on `Detalhamento` + `POST /auditoria` (triggers `AuditoriaService.processar`).               |
| `/regras`        | `regra_router.py`       | CRUD on `RegraGrupo` (`GET /grupos`, `GET /grupos/all`, `GET /grupos/{id}`, `POST /grupos`, `PUT /grupos/{id}`, `DELETE /grupos/{id}`) — see "Detalhamento & Auditoria" below. |

**Key domain models:**

- `Lancamento`: Financial transaction (RECEITA/DESPESA), payment form (PIX/DINHEIRO/CARTAO_CREDITO/CARTAO_DEBITO), status (CONCILIADO/NAO_CONCILIADO), a deduplication `hash_transacao`, and computed `quantidade_detalhamentos`/`soma_detalhamentos` (column_property, no N+1)
- `Finalidade`: Category/purpose for a transaction — full CRUD via API; seeds provide initial data at startup ("INSCRIÇÃO" is a single unified finalidade, not split by encontreiro/encontrista)
- `UploadFile` (table `uploads`): Generic uploaded-file record — used by all three CSV import flows (conciliação, encontreiros, encontristas), not conciliação-specific. Fields: `nome_arquivo, conteudo_csv, tamanho_bytes, processado_em, status(PROCESSANDO/PROCESSADO/ERRO), error_code, error_message, resultado_processamento` (JSON string: `inseridos/duplicados/erros/detalhes_erros/mensagem`)
- `Usuario`: Authenticated user with `perfil` (ADMINISTRADOR/CONCILIADOR/REPORTER/SECRETARIO) — read-only via API, managed via seeds
- `Encontreiro`/`Encontrista`: Rich registration records (personal, contact, medical/emergency, payment fields). `Encontrista.padrinho_id` FKs to an `Encontreiro` (required sponsor). Both have a computed `auditado` (column_property EXISTS against `Detalhamento`)
- `Equipe`/`Circulo`: Lookup groups — Encontreiros belong to an `Equipe` (with `acesso`: EDG/VERMELHO/AMARELO/VERDE), Encontristas belong to a `Circulo` (with a display `rgb` color)
- `Detalhamento`: Line-item breakdown of what a `Lancamento` pays for — `tipo` is `INSCRICAO_ENCONTREIRO`/`INSCRICAO_ENCONTRISTA` (with `referencia_id` pointing to the person) or `OFERTA`/`OUTRO` (free-text `descricao`). One lançamento can have several (e.g. one PIX covering an inscription + an offering)
- `RegraGrupo`/`Regra`/`RegraCondicao`: the configurable "motor de regras" that drives the Etapa B (Extração) of Auditoria — see "Detalhamento & Auditoria" below for the full model

### Authentication

All routes except `POST /auth/login` and `GET /health` require a JWT bearer token.
Token obtained via `POST /auth/login`. Dependency `get_current_user` in `core/deps.py` validates it on every protected request.
Users are seeded at startup — no registration endpoint. `perfil` values: `ADMINISTRADOR`, `CONCILIADOR`, `REPORTER`, `SECRETARIO`.

### Deduplication Logic

Hashes are generated by `gerar_hash(descricao, valor, data, observacao)` (`app/utils/hash_utils.py`) from `descricao_normalizada + valor + data_pagamento + observacao_normalizada` (SHA-256). A unique constraint on `hash_transacao` in the DB prevents duplicates. The service layer checks before insert and the reconciliation engine (`Conciliador`) uses the same logic when processing CSV imports.

**Important nuance for Banco Inter statements**: `BancoInterParser` no longer folds the row's account balance ("Saldo") into `observacao` — that column is parsed but otherwise unused. Instead, it counts occurrences of each `(descricao, data, valor)` combination *within the current file being processed* (a plain in-memory counter, reset on every `parse()` call). When the same combination repeats in the same file, `observacao` gets a `| ocor: N` suffix before hashing — this is what differentiates genuinely distinct same-day/same-value payments (e.g. an inscription paid in two installments) so they don't collide on hash and get wrongly rejected as duplicates. Because the counter always restarts from zero for each processing run, re-uploading the exact same file reproduces the exact same sequence of `ocor: N` suffixes, so real duplicates — whether from re-uploading a file or overlapping date ranges across different processing runs — still hash identically and are correctly caught by the `hash_transacao` uniqueness check.

### CSV Upload Flow (shared by Conciliação, Encontreiros, Encontristas)

`POST /conciliacao/upload` | `POST /encontreiros/conciliacao` | `POST /encontristas/conciliacao` → `*Service.iniciar_conciliacao()` creates an `UploadFile` row (status `PROCESSANDO`) synchronously, then a FastAPI background task runs `*Service.processar_em_background()`, which parses the file, dedupes, inserts new records, and writes `resultado_processamento` (JSON: `inseridos`, `duplicados`, `erros`, `detalhes_erros` — each `{linha, descricao, erro}` with the real CSV line number — and a summary `mensagem`) plus final `status` (`PROCESSADO`/`ERRO`).

The frontend polls `GET /uploads/{id}/status` (lightweight — no `conteudo_csv`) until status leaves `PROCESSANDO`, then fetches the full record via `GET /uploads/{id}`. Currently only the Banco Inter CSV format is supported for bank statements (`ParserFactory`).

After bank import, `Lancamento` records are `NAO_CONCILIADO`. Manual reconciliation via `PATCH /lancamentos/conciliar/{id}/finalidade/{fid}`.

### Detalhamento & Auditoria

A `Lancamento` isn't automatically "who paid for what" — that link is a `Detalhamento`. Validation (`DetalhamentoService`) enforces the sum of a lançamento's detalhamentos never exceeds its `valor` (tolerance `0.01`).

`POST /detalhamentos/auditoria` (`AuditoriaService.processar`, `app/services/auditoria_service.py`) is a batch matching pass over every Encontreiro/Encontrista with a pending payment (`pagamento > 0`, `dt_pagamento` set, not yet `auditado`). It also runs automatically after a successful bank/encontreiro/encontrista CSV import (`status == PROCESSADO`), best-effort (a failure here never flips the upload's own status). Per pendência, it runs two conceptually separate steps:

- **Etapa A — Match** (`app/integracao/regras/motor_match.py`, fixed algorithm, not configurable): finds same-day RECEITA `Lancamento` candidates (already filtered in SQL to `NAO_CONCILIADO` and `valor >= pagamento`) whose remaining capacity (`valor - soma_detalhamentos`) fits the `pagamento` and whose `nome_pagador` (case/accent-insensitive) appears in the lançamento's `descricao` (never `observacao`). Candidates are then filtered by `Lancamento.forma_pagamento` matching the forma de pagamento recognizable in the pendência's `observacao` (pix/dinheiro/cartão de crédito/cartão de débito — "cartão" alone means crédito, "espécie" is a synonym for dinheiro); if the observação doesn't mention any recognizable forma, PIX is assumed (the most common case) rather than skipping this filter. Ties broken by lowest `Lancamento.id`.
- **Etapa B — Extração** (`app/integracao/regras/motor_extracao.py`, configurable via the `motor de regras`): once a lançamento is found, reads the pendência's own `observacao` to decide how many `Detalhamento`s to create and of what type/value, using the active `RegraGrupo`/`Regra`/`RegraCondicao` tree for the pendência's escopo (`RegraRepository.list_ativos_por_escopos`). If nothing matches, falls back to 1 Detalhamento for the full `pagamento` (today's implicit behavior).

**Motor de regras model**: one `RegraGrupo` per `EscopoRegraGrupo` (`EXTRACAO_ENCONTREIRO`, `EXTRACAO_ENCONTRISTA` — `OFERTAS` is a legacy escopo value kept in the enum for backward compatibility but no longer seeded/consulted; Oferta rules now live inside the same group as Inscrição). Each `Regra` produces at most 1 `Detalhamento` and has a `modo_extracao`:
- `TOKEN_VALOR` (default): all of its `RegraCondicao.padrao_regex` must match (AND) against the normalized `observacao` (accents stripped, lowercased); the value comes from the first non-empty capture group, in order.
- `NOME_NA_LISTA`: ignores `RegraCondicao` entirely — anchors on the first word of the pendência's own `nome` (not `nome_pagador`) in the observação, then walks word-by-word toward the value: each intervening word must either be contained in the person's own `nome` (accent/case-insensitive substring, so a partial word like "ourado" from "Dourado" still counts) or be a common Portuguese connector (de/da/do/das/dos/e/para/no/na); any other word makes the match ambiguous and the function returns no value instead of guessing. Covers a single payment covering several named inscriptions in one shared observação (e.g. `"...para Luiza Rochelle de 100 reais, Samuel Augusto de 100 reais..."`).

"Stop on first match" applies **per `tipo_detalhamento_resultado`**, not per group: within the same tipo (e.g. two Inscrição rules), only the first Regra (by `ordem`) that matches counts; different tipos (Inscrição vs Oferta) are evaluated independently and can both fire from the same observação. A `Regra` can only be `ativo` if it has ≥1 `RegraCondicao` (except `NOME_NA_LISTA`, which never needs one) — enforced both in the repository (`_montar_regra`/`_sincronizar_ativo_grupo` in `app/repositories/regra_repository.py`) and in the frontend UI. A `RegraGrupo` can't be `ativo` without ≥1 `Regra` ativa; this only ever auto-*deactivates* the group, never auto-activates it.

`app/database/seeds/seed_regras.py` seeds default Regras per escopo, and — since a `RegraGrupo` only gets created once per escopo (`if existente: continue`) — separately backfills already-existing grupos with any default Regra (matched by `nome`) they don't yet have, so a new default rule still reaches environments that were seeded before it existed. `EXTRACAO_ENCONTRISTA` has two extra default Regras `EXTRACAO_ENCONTREIRO` doesn't: "Inscrição (valor no pagamento)" (`TOKEN_VALOR`, reads the value right after `"pagamento via ... de"` — evidence straight from the observação instead of trusting the registered `pagamento`) and "Biscoitos" (`TOKEN_VALOR`, `tipo_detalhamento_resultado=OUTRO` — a value near "biscoito" counts unless "pacote(s)"/"pct" appears anywhere in the observação, meaning physical delivery rather than a charge). Biscoitos' third `RegraCondicao` reuses the "Inscrição (valor no pagamento)" pattern *without* a capture group, purely as a gate: since `_valor_com_regex` only takes the value from the first condição with a capture, a condição can be added just to require some other evidence be present without affecting which value gets used. This is how "Oferta/Biscoito never fire alone" is enforced — if the observação doesn't also state the inscription's own value, the gate condição fails and no Detalhamento (not even the fallback) is created for that Regra.

Returns counts (`avaliados`, `vinculados_encontreiro`, `vinculados_encontrista`, `detalhamentos_extras_via_observacao`, `nao_auditados`, `detalhes_nao_auditados`, `mensagem`).

### Dashboard Endpoints

`GET /dashboard/totais` — aggregated totals (receitas, despesas, saldo, quantidade).
`GET /dashboard/por-dia` — day-by-day breakdown for a period.
`GET /dashboard/por-mes` — month-by-month breakdown for a period.
`GET /dashboard/por-finalidade` — totals grouped by finalidade (id, nome, total_valor, quantidade).
All share the same filter DTO: `data_inicio`, `data_fim` (defaults: today → today+30d), `forma_pagamento[]`, `finalidade_id[]`, `tipo`, `status`.

### Relatórios (PDF)

`GET /relatorios/livro-caixa` and `GET /relatorios/resumo-geral` generate PDF reports for a date range.

## Key Config Locations

- **All env vars**: `app/core/config.py` — single source of truth, plain `os.getenv` module-level constants (no pydantic Settings class)
- **Local dev env**: `.env` (gitignored) — copy from `.env.example`
- **Python deps**: `requirements.txt`
- **DB schema**: managed via Alembic migrations (`alembic/versions/`, 16+ revisions) — auto-applied on startup by the lifespan handler, also run explicitly on Render deploy
- **Seed data**: `app/database/seeds/` — runs on startup, idempotent
- **Deploy**: `render.yaml` (Render Blueprint — web service, runs `alembic upgrade head` on build)

## Environment Variables Reference

| Variable            | Default                                                       | Purpose                                                                                             |
| --------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `DATABASE_URL`      | `postgresql://db_financeiro:fin_pass@localhost:5432/financeiro_encontro` | DB connection string                                                                                |
| `APP_PORT`          | `8000`                                                          | Port uvicorn listens on                                                                              |
| `APP_VERSION`       | `0.4.0`                                                         | App version, shown in `/health`                                                                     |
| `JWT_SECRET`        | `changeme-insecure-secret`                                      | JWT signing key — always override in production                                                    |
| `JWT_ALGORITHM`     | `HS256`                                                         | JWT algorithm                                                                                         |
| `JWT_EXPIRE_MINUTES`| `480`                                                           | Token expiry (8 hours)                                                                                |
| `SQL_ECHO`          | `false`                                                         | Log all SQL queries to console — enable in development only                                         |
| `CORS_ORIGINS`      | `http://localhost:4200`                                         | Allowed CORS origins (comma-separated) — set to the `financeiro-encontro-web` deployed URL in production |

Note: `UPLOAD_FOLDER` from the previous version of this doc no longer applies — uploaded CSV content is stored directly in the `uploads.conteudo_csv` DB column, not on disk.
