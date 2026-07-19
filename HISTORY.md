# Histórico de Versões

## [0.0.1] — 2026-07-18

### Adicionado
- Repositório extraído do monorepo `financeiro-encontro` como projeto independente
- API FastAPI para gestão financeira de eventos: autenticação JWT, CRUD de lançamentos (receita/despesa) e finalidades
- Conciliação de extratos bancários via importação de CSV (parser dedicado ao Banco Inter) com deduplicação por hash
- Endpoints de dashboard (totais, por dia, por mês, por finalidade) e relatórios (livro-caixa, resumo-geral)
- Controle de acesso por perfil de usuário
- Migrations via Alembic e seeds idempotentes para dados iniciais
