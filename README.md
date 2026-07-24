# Financeiro Encontro — Backend

Backend do sistema **Financeiro Encontro**, responsável por gerenciar toda a lógica financeira do evento.

Este serviço fornece uma API REST para controle de:

- Entradas e saídas financeiras
- Formas de pagamento (PIX, dinheiro, cartão)
- Finalidades (oferta, campanha, inscrição)
- Importação e conciliação de extratos bancários via CSV
- Geração de relatórios PDF (Livro Caixa e Resumo Geral)
- CRUD de usuários com perfis de acesso (ADMINISTRADOR, CONCILIADOR, REPORTER)

---

## Tecnologias Utilizadas

- Python 3.11
- FastAPI
- SQLAlchemy 2.0
- Pydantic v2
- PostgreSQL 15
- Pandas (processamento de CSV)
- Docker

---

## Arquitetura

O backend segue uma **arquitetura em camadas**, separando responsabilidades:

```
app/
│
├── core/          # Configurações e exceções customizadas
├── database/      # Sessão do banco e seeds de dados
├── models/        # Entidades ORM (SQLAlchemy)
├── schemas/       # Validação de dados (Pydantic) e DTOs de filtro
├── repositories/  # Acesso ao banco de dados
├── services/      # Regras de negócio
├── routers/       # Endpoints HTTP
├── integracao/    # Parser de CSV e engine de conciliação
├── utils/         # Funções auxiliares (hash, sorting)
│
└── main.py        # Inicialização da aplicação
```

Fluxo de uma requisição:

```
Request → Router → Service → Repository → Banco
```

---

## Banco de Dados

- PostgreSQL 15
- Schema gerenciado via **Alembic** (migrations versionadas)
- Seeds de dados executados no startup (finalidades padrão)

⚠️ O backend **depende do banco rodando via Docker** antes de ser iniciado.

---

## Como rodar

Este repositório assume que os repositórios irmãos `financeiro-encontro-web` e `infra-encontro` estão clonados lado a lado (mesma pasta pai).

### 1. Subir o banco

```bash
docker compose -f ../infra-encontro/docker-compose-db.yml up -d
```

### 2. Rodar o backend

```bash
./start-backend.sh
```

O script faz automaticamente:

- Cria o venv (se não existir)
- Ativa o ambiente virtual
- Instala dependências
- Carrega o `.env` se existir na pasta `backend/`
- Inicia o servidor FastAPI na porta definida por `APP_PORT` (padrão: 8000)

---

## Variáveis de Ambiente

O `.env.example` deste repositório cobre o desenvolvimento local via `./start-backend.sh`. Para subir a stack completa com Docker Compose (banco + backend + frontend), use o `.env.example` do repositório [`infra-encontro`](https://github.com/encontro-plataforma/infra-encontro).

### Configurando para desenvolvimento local

```bash
cp .env.example .env
# edite .env com os valores reais
```

### Variáveis disponíveis

| Variável | Descrição | Padrão | Obrigatória |
|---|---|---|---|
| `DATABASE_URL` | URL de conexão com o banco | `postgresql://...@localhost:5432/financeiro_encontro` | Sim |
| `APP_PORT` | Porta em que o servidor sobe | `8000` | Não |
| `APP_VERSION` | Versão da aplicação exibida no startup e no health check | `0.1.0` | Não |
| `JWT_SECRET` | Chave secreta para assinar os tokens | `changeme-insecure-secret` | **Sim em produção** |
| `JWT_ALGORITHM` | Algoritmo de assinatura JWT | `HS256` | Não |
| `JWT_EXPIRE_MINUTES` | Expiração do token em minutos | `480` (8 horas) | Não |
| `SQL_ECHO` | Exibe queries SQL no console | `false` | Não |
| `CORS_ORIGINS` | Origens permitidas (separadas por vírgula) | `http://localhost:4200` | Não |

> ⚠️ O arquivo `.env` está no `.gitignore` e **nunca deve ser commitado**. Apenas `.env.example` é versionado.

> ⚠️ Em produção, sempre defina um `JWT_SECRET` forte. Para gerar:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## Versão da aplicação

A versão do backend é centralizada em `app/core/config.py` e usada em três pontos:

- na inicialização da aplicação, com log no startup
- no metadata do FastAPI (`app.version`)
- no endpoint `GET /health`, que retorna também a versão atual

O valor padrão é `0.1.0`, mas pode ser sobrescrito por meio da variável `APP_VERSION`.

Exemplo:

```bash
APP_VERSION=0.6.0 ./start-backend.sh
```

---

## Acessos

| Serviço | URL |
|---|---|
| API | `http://localhost:{APP_PORT}` |
| Swagger | `http://localhost:{APP_PORT}/docs` |
| Health Check | `http://localhost:{APP_PORT}/health` (retorna `status` e `version`) |

---

## Autenticação

Todas as rotas — exceto `/auth/login` e `/health` — exigem um token JWT no header:

```
Authorization: Bearer <token>
```

O token é obtido via `POST /auth/login`. Por padrão expira em **8 horas** (configurável via `JWT_EXPIRE_MINUTES`).

### Autenticação `/auth`

| Método | Rota | Descrição | Pública |
|---|---|---|---|
| POST | `/auth/login` | Gera token JWT | Sim |
| GET | `/auth/me` | Retorna usuário autenticado | Não |

---

## Perfis de Acesso (RBAC)

O campo `perfil` do usuário controla o que cada um pode ver e fazer.

| Perfil | Descrição |
|---|---|
| `ADMINISTRADOR` | Acesso total — lançamentos, conciliação, arquivos, finalidades, usuários e relatórios |
| `CONCILIADOR` | Acesso financeiro — lançamentos, conciliação e arquivos. Sem telas de administração |
| `REPORTER` | Somente Dashboard (sem navegar para lançamentos) e Relatórios |

Regras de negócio no CRUD de usuários:
- O usuário de ID `1` (administrador principal) **nunca pode ser excluído**
- Nenhum usuário pode **excluir a si mesmo**
- Usuários são gerenciados via `POST/PUT/DELETE /usuarios` (requer autenticação)

---

## Endpoints

### Lançamentos `/lancamentos`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/lancamentos/` | Listar com paginação e filtros |
| GET | `/lancamentos/all` | Listar todos sem paginação |
| GET | `/lancamentos/{id}` | Buscar por ID |
| POST | `/lancamentos/` | Criar lançamento |
| PUT | `/lancamentos/{id}` | Atualizar lançamento |
| DELETE | `/lancamentos/{id}` | Excluir lançamento |
| PATCH | `/lancamentos/conciliar-lancamento/{id}?idFinalidade={id}` | Conciliar manualmente um lançamento |

**Filtros disponíveis no GET `/lancamentos/`:**
- `data_inicio` / `data_fim` — intervalo de data de pagamento
- `status` — `CONCILIADO` ou `NAO_CONCILIADO`
- `tipo` — `RECEITA` ou `DESPESA`
- `finalidade_id` — ID de uma finalidade específica
- `forma_pagamento[]` — `PIX`, `DINHEIRO`, `CARTAO_CREDITO`, `CARTAO_DEBITO`
- `descricao` — busca parcial na descrição
- `skip` / `limit` — paginação
- `sort` — ordenação (ex: `data_pagamento:desc`)

---

### Finalidades `/finalidades`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/finalidades/` | Listar com paginação e filtros |
| GET | `/finalidades/all` | Listar todas sem paginação |
| GET | `/finalidades/{id}` | Buscar por ID |
| POST | `/finalidades/` | Criar finalidade |
| PUT | `/finalidades/{id}` | Atualizar finalidade |
| DELETE | `/finalidades/{id}` | Excluir finalidade |

**Filtros disponíveis no GET `/finalidades/`:**
- `nome` — filtro por nome (parcial)
- `tipo` — `RECEITA` ou `DESPESA`

---

### Extratos Bancários `/extratos-bancarios`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/extratos-bancarios/` | Listar com paginação e filtros |
| GET | `/extratos-bancarios/all` | Listar todos sem paginação |
| GET | `/extratos-bancarios/{id}` | Buscar por ID |
| DELETE | `/extratos-bancarios/{id}` | Excluir extrato |

**Filtros disponíveis:**
- `nome_arquivo` — filtro por nome do arquivo
- `processado_em_inicio` / `processado_em_fim` — intervalo de data de processamento

---

### Dashboard `/dashboard`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/dashboard/totais` | Totais agregados (receitas, despesas, saldo, quantidade) |
| GET | `/dashboard/por-dia` | Breakdown dia a dia para um período |
| GET | `/dashboard/por-mes` | Breakdown mês a mês para um período |
| GET | `/dashboard/por-finalidade` | Totais agrupados por finalidade |

**Filtros disponíveis (compartilhados por todos os endpoints):**
- `data_inicio` / `data_fim` — intervalo de datas (padrão: hoje → hoje+30d)
- `forma_pagamento[]` — `PIX`, `DINHEIRO`, `CARTAO_CREDITO`, `CARTAO_DEBITO`
- `finalidade_id[]` — lista de IDs de finalidade
- `tipo` — `RECEITA` ou `DESPESA`
- `status` — `CONCILIADO` ou `NAO_CONCILIADO`

---

### Conciliação `/conciliacao`

| Método | Rota | Descrição |
|---|---|---|
| POST | `/conciliacao/upload` | Upload e processamento de CSV bancário (limite: 3 MB) |

---

### Usuários `/usuarios`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/usuarios/` | Listar usuários |
| GET | `/usuarios/{id}` | Buscar por ID |
| POST | `/usuarios/` | Criar usuário |
| PUT | `/usuarios/{id}` | Atualizar usuário |
| DELETE | `/usuarios/{id}` | Excluir usuário (restrições: id=1 e self) |

**Campos:** `nome`, `email`, `senha` (hash bcrypt), `ativo`, `perfil` (`ADMINISTRADOR` \| `CONCILIADOR` \| `REPORTER`).

---

### Relatórios `/relatorios`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/relatorios/livro-caixa` | PDF contábil com todas as entradas, saídas e saldo acumulado |
| GET | `/relatorios/resumo-geral` | PDF com tabelas pivot de Receitas e Despesas por forma de pagamento e finalidade, com linha de saldo |

**Parâmetros comuns:** `data_inicio` (YYYY-MM-DD) e `data_fim` (YYYY-MM-DD).

> O relatório **Resumo Geral** agrupa as finalidades em categorias fixas. Os IDs e nomes das finalidades padrão (`seed_finalidade.py`) não podem ser alterados sem também atualizar `relatorio_service.py`.

---

## Fluxo de Conciliação via CSV

1. Upload de CSV (formato Banco Inter) via `POST /conciliacao/upload`
2. Backend valida e processa o arquivo
3. Cria lançamentos automaticamente como `NAO_CONCILIADO`
4. Aplica sugestão automática de finalidade por palavras-chave
5. Retorna relatório com totais de inseridos, duplicados e erros
6. Usuário concilia manualmente via `PATCH /lancamentos/conciliar-lancamento/{id}`

### Deduplicação

Cada lançamento gera um hash SHA-256 a partir de `descricao_normalizada + valor + data_pagamento`. Reenviar o mesmo CSV não duplica registros.

---

## Migrations (Alembic)

Os comandos abaixo devem ser executados dentro da pasta `backend/` com o venv ativo.

> A URL do banco é lida automaticamente da variável `DATABASE_URL` (via `alembic/env.py`). O `alembic.ini` não precisa ser editado.
>
> Ao rodar `alembic` diretamente no terminal (fora do `start-backend.sh`), carregue o `.env` antes:
> ```bash
> export $(grep -v '^#' .env | xargs) && alembic upgrade head
> ```

### Aplicar todas as migrations pendentes

```bash
alembic upgrade head
```

### Gerar nova migration a partir das mudanças nos models

```bash
alembic revision --autogenerate -m "descricao da mudanca"
```

> Sempre revise o arquivo gerado em `alembic/versions/` antes de aplicar — o autogenerate não detecta tudo (ex: renomeações de coluna).

### Reverter a última migration

```bash
alembic downgrade -1
```

### Ver histórico de migrations

```bash
alembic history
```

### Ver qual migration está aplicada no banco

```bash
alembic current
```

---

## Problemas comuns

**Erro de conexão com o banco:**

```
could not connect to server
```

Solução: subir o banco antes do backend.

```bash
docker compose -f ../infra-encontro/docker-compose-db.yml up -d
```

---

## Próximos passos

- Suporte a outros bancos no parser de CSV (Itaú, Bradesco, Santander)
