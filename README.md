# Financeiro Encontro — Backend

Backend do sistema **Financeiro Encontro**, responsável por gerenciar toda a lógica financeira do evento.

Este serviço fornece uma API REST para controle de:

- Entradas e saídas financeiras
- Formas de pagamento (PIX, dinheiro, cartão)
- Finalidades (oferta, campanha, inscrição)
- Importação e conciliação de extratos bancários via CSV
- Secretaria: cadastro de Encontreiros/Encontristas (via CSV), Equipes e Círculos
- Detalhamentos: vínculo entre um lançamento de RECEITA e uma ou mais inscrições (ou oferta/outros
  valores), com auditoria manual (`POST /detalhamentos/auditoria`) para casar pagamentos pendentes
  automaticamente
- Geração de relatórios PDF (Livro Caixa e Resumo Geral)
- CRUD de usuários com perfis de acesso (ADMINISTRADOR, CONCILIADOR, REPORTER, SECRETARIO)

---

## Tecnologias Utilizadas

- Python 3.11
- FastAPI
- SQLAlchemy 2.0
- Pydantic v2
- PostgreSQL 15
- Pandas (processamento de CSV)
- Docker
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes e ambiente virtual)

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

- Carrega o `.env` se existir na pasta `backend/`
- Sincroniza as dependências com `uv sync` (cria/atualiza o `.venv` a partir do `pyproject.toml`/`uv.lock`)
- Inicia o servidor FastAPI (`uv run fastapi dev`, com reload automático) na porta definida por `APP_PORT` (padrão: 8000)

### Rodando sem o script

As dependências são gerenciadas via [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`), não mais `requirements.txt`. Os comandos equivalentes ao script, na mão:

```bash
uv sync                        # cria o .venv e instala as dependências (main + dev)
uv run fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

> `fastapi dev` (do pacote `fastapi-cli`, dependência de dev) é o CLI oficial do FastAPI para desenvolvimento local — já vem com reload automático. Em produção (Docker/Render) continua-se usando `uvicorn` diretamente, sem o `fastapi-cli`.

`uv run <comando>` executa qualquer comando já dentro do `.venv` do projeto, sem precisar ativar (`source .venv/bin/activate`) — mas ativar continua funcionando normalmente se preferir.

Para adicionar uma nova dependência:

```bash
uv add nome-do-pacote           # dependência de produção
uv add --group dev nome-do-pacote  # dependência só de desenvolvimento (ex: ruff)
```

Isso atualiza `pyproject.toml` e `uv.lock` automaticamente — ambos devem ser commitados.

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
| `APP_VERSION` | Versão da aplicação exibida no startup e no health check | `0.3.0` | Não |
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

O valor padrão é `0.3.0`, mas pode ser sobrescrito por meio da variável `APP_VERSION`.

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
| `SECRETARIO` | Módulo Secretaria — Encontreiros, Encontristas, Equipes e Círculos |

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
| PATCH | `/lancamentos/conciliar/{lancamento_id}/finalidade/{finalidade_id}` | Conciliar manualmente um lançamento |

**Filtros disponíveis no GET `/lancamentos/`:**
- `data_inicio` / `data_fim` — intervalo de data de pagamento
- `status` — `CONCILIADO` ou `NAO_CONCILIADO`
- `tipo` — `RECEITA` ou `DESPESA`
- `finalidade_id` / `finalidade_ids[]` — uma finalidade ou uma lista de finalidades
- `forma_pagamento[]` — `PIX`, `DINHEIRO`, `CARTAO_CREDITO`, `CARTAO_DEBITO`
- `descricao` — busca parcial na descrição
- `exclude_ids[]` — exclui IDs já carregados (usado na paginação incremental da tela de Conciliação)
- `skip` / `limit` — paginação
- `sort` — ordenação (ex: `data_pagamento:desc`)

**Corpo do `PATCH /lancamentos/conciliar/{lancamento_id}/finalidade/{finalidade_id}`** (todos os campos opcionais):

```json
{
  "observacao": "texto livre, sobrescreve a observação do lançamento",
  "detalhamento_final": { "descricao": "Oferta" }
}
```

Para lançamentos de RECEITA, o backend valida antes de conciliar: a soma dos `Detalhamento`s vinculados
não pode ultrapassar o valor do lançamento, e se a finalidade escolhida for "INSCRIÇÃO" é obrigatório já
existir ao menos um Detalhamento de inscrição vinculado. Se sobrar valor (`valor do lançamento - soma dos
detalhamentos > 0`) e `detalhamento_final` for enviado, um Detalhamento extra é criado automaticamente
(`OFERTA` se a finalidade for "OFERTA", senão `OUTRO`) com esse valor. Lançamentos de DESPESA não têm
Detalhamentos — a conciliação apenas define a finalidade e o status.

`LancamentoResponse` também expõe `quantidade_detalhamentos` e `soma_detalhamentos` (calculados, sem
necessidade de consultar `/detalhamentos` separadamente).

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

### Uploads (extratos/CSVs) `/uploads`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/uploads/` | Listar com paginação e filtros |
| GET | `/uploads/all` | Listar todos sem paginação |
| GET | `/uploads/{id}` | Buscar por ID (inclui `status` e `resultado_processamento`) |
| GET | `/uploads/{id}/download` | Baixar o CSV original enviado |
| DELETE | `/uploads/{id}` | Excluir upload |

**Filtros disponíveis:**
- `nome_arquivo` — filtro por nome do arquivo
- `processado_em_inicio` / `processado_em_fim` — intervalo de data de processamento

Usado tanto para extratos bancários (`/conciliacao/upload`) quanto para os CSVs de Encontreiro/Encontrista
(`/encontreiros/conciliacao`, `/encontristas/conciliacao`) — todos processados de forma assíncrona
(`status`: `PROCESSANDO` → `PROCESSADO`/`ERRO`).

---

### Secretaria — Encontreiros `/encontreiros`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/encontreiros/` | Listar com paginação e filtros |
| GET | `/encontreiros/all` | Listar todos sem paginação |
| GET | `/encontreiros/{id}` | Buscar por ID (inclui `auditado`, `detalhamento_id`, `lancamento_vinculado`) |
| POST | `/encontreiros/` | Criar encontreiro |
| PUT | `/encontreiros/{id}` | Atualizar encontreiro |
| DELETE | `/encontreiros/{id}` | Excluir encontreiro |
| POST | `/encontreiros/conciliacao` | Upload de CSV (assíncrono) — cria/atualiza registros e roda a auditoria ao final |

**Filtros disponíveis no GET `/encontreiros/`:**
- `nome` / `apelido` / `nome_ou_apelido` — busca parcial
- `equipe_nome` / `equipe_acesso` / `equipe_ids[]`
- `situacao_camisa[]` — `PENDENTE`, `SOLICITADA`, `RECEBIDA`, `ENTREGUE`, `SEM_BLUSA`
- `auditado` — `true`/`false` (já foi vinculado a um lançamento via Detalhamento)
- `dt_inscricao_inicio` / `dt_inscricao_fim`

---

### Secretaria — Encontristas `/encontristas`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/encontristas/` | Listar com paginação e filtros |
| GET | `/encontristas/all` | Listar todos sem paginação |
| GET | `/encontristas/padrinhos-disponiveis` | Lista de Encontreiros elegíveis como padrinho |
| GET | `/encontristas/{id}` | Buscar por ID (inclui `auditado`, `detalhamento_id`, `lancamento_vinculado`) |
| POST | `/encontristas/` | Criar encontrista |
| PUT | `/encontristas/{id}` | Atualizar encontrista |
| DELETE | `/encontristas/{id}` | Excluir encontrista |
| POST | `/encontristas/conciliacao` | Upload de CSV (assíncrono) — cria/atualiza registros e roda a auditoria ao final |

**Filtros disponíveis no GET `/encontristas/`:**
- `nome` / `apelido` / `nome_ou_apelido` — busca parcial
- `circulo_nome` / `circulo_ids[]` (`0` = sem círculo) / `padrinho_id`
- `auditado` — `true`/`false`
- `camisa` / `blusa` / `carta` / `album`
- `dt_entrega_inicio` / `dt_entrega_fim`, `dt_nascimento_inicio` / `dt_nascimento_fim`

---

### Secretaria — Equipes `/equipes`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/equipes/` | Listar com paginação e filtros |
| GET | `/equipes/all` | Listar todas sem paginação |
| GET | `/equipes/{id}` | Buscar por ID |
| POST | `/equipes/` | Criar equipe |
| PUT | `/equipes/{id}` | Atualizar equipe |
| DELETE | `/equipes/{id}` | Excluir equipe |

---

### Secretaria — Círculos `/circulos`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/circulos/` | Listar com paginação e filtros |
| GET | `/circulos/all` | Listar todos sem paginação |
| GET | `/circulos/{id}` | Buscar por ID |
| POST | `/circulos/` | Criar círculo |
| PUT | `/circulos/{id}` | Atualizar círculo |
| DELETE | `/circulos/{id}` | Excluir círculo |

---

### Detalhamentos `/detalhamentos`

Um `Detalhamento` liga parte do valor de um `Lancamento` de RECEITA a uma inscrição de
Encontreiro/Encontrista, ou marca esse valor como `OFERTA`/`OUTRO`. Lançamentos de DESPESA não têm
Detalhamentos.

| Método | Rota | Descrição |
|---|---|---|
| GET | `/detalhamentos/` | Listar com paginação e filtros |
| GET | `/detalhamentos/all` | Listar todos sem paginação |
| GET | `/detalhamentos/{id}` | Buscar por ID |
| POST | `/detalhamentos/` | Criar detalhamento |
| PUT | `/detalhamentos/{id}` | Atualizar detalhamento |
| DELETE | `/detalhamentos/{id}` | Excluir detalhamento (a inscrição volta a ficar pendente de auditoria) |
| POST | `/detalhamentos/auditoria` | Roda a auditoria manualmente: tenta casar todo Encontreiro/Encontrista pendente (`auditado=false`, com pagamento e data registrados) a um lançamento de RECEITA compatível |

**Filtros disponíveis no GET `/detalhamentos/`:**
- `lancamento_id` / `tipo` (`INSCRICAO_ENCONTREIRO`, `INSCRICAO_ENCONTRISTA`, `OFERTA`, `OUTRO`) / `referencia_id`

`DetalhamentoResponse` inclui `detalhe_nome` (nome da pessoa ou o label do tipo) e `observacao_efetiva`
(para inscrições, vem ao vivo da observação do Encontreiro/Encontrista referenciado).

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

**Campos:** `nome`, `email`, `senha` (hash bcrypt), `ativo`, `perfil` (`ADMINISTRADOR` \| `CONCILIADOR` \| `REPORTER` \| `SECRETARIO`).

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

1. Upload de CSV (formato Banco Inter) via `POST /conciliacao/upload` — responde na hora com `{upload_id, status}` e processa em segundo plano
2. Backend valida e processa o arquivo (`GET /uploads/{upload_id}` para acompanhar o `status` e o resumo)
3. Cria lançamentos automaticamente como `NAO_CONCILIADO`
4. Aplica sugestão automática de finalidade por palavras-chave/valor (`sugestao_finalidade_id`)
5. Retorna relatório com totais de inseridos, duplicados e erros
6. Para lançamentos de RECEITA, o usuário pode rodar `POST /detalhamentos/auditoria` para tentar vincular
   automaticamente inscrições de Encontreiro/Encontrista pendentes (ver seção Detalhamentos)
7. Usuário concilia manualmente via `PATCH /lancamentos/conciliar/{lancamento_id}/finalidade/{finalidade_id}`

### Deduplicação

Cada lançamento gera um hash SHA-256 a partir de `descricao_normalizada + valor + data_pagamento`. Reenviar o mesmo CSV não duplica registros.

---

## Migrations (Alembic)

Os comandos abaixo devem ser executados dentro da pasta `backend/`, prefixados com `uv run` (não é necessário ativar o `.venv` manualmente).

> A URL do banco é lida automaticamente da variável `DATABASE_URL` (via `alembic/env.py`). O `alembic.ini` não precisa ser editado.
>
> Ao rodar `alembic` diretamente no terminal (fora do `start-backend.sh`), carregue o `.env` antes:
> ```bash
> export $(grep -v '^#' .env | xargs) && uv run alembic upgrade head
> ```

### Aplicar todas as migrations pendentes

```bash
uv run alembic upgrade head
```

### Gerar nova migration a partir das mudanças nos models

```bash
uv run alembic revision --autogenerate -m "descricao da mudanca"
```

> Sempre revise o arquivo gerado em `alembic/versions/` antes de aplicar — o autogenerate não detecta tudo (ex: renomeações de coluna).

### Reverter a última migration

```bash
uv run alembic downgrade -1
```

### Ver histórico de migrations

```bash
uv run alembic history
```

### Ver qual migration está aplicada no banco

```bash
uv run alembic current
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
