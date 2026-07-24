# Histórico de Versões

## [0.1.0] — 2026-07-24

### Adicionado
- Módulo Secretaria: entidades `Equipe` e `Círculo` com CRUD completo, seeds padrão e novo perfil de
  usuário `SECRETARIO`

### Alterado
- `ExtratoBancario` renomeado para `UploadFile` (tabela `uploads`, rota `/uploads`), generalizando o
  serviço de upload de arquivos para os próximos módulos; agora registra `error_code`/`error_message`
  quando o processamento de um arquivo falha

### Adicionado
- Módulo Secretaria: entidade `Encontreiro` com CRUD completo e conciliação via importação de CSV
  (`POST /encontreiros/conciliacao`), com atualização de cadastros existentes por ID, deduplicação por
  nome+telefone e validação de equipe
- Módulo Secretaria: entidade `Encontrista` com CRUD completo e conciliação via importação de CSV
  (`POST /encontristas/conciliacao`), vinculada a um Encontreiro padrinho (obrigatório) e a um Círculo
  (opcional)
- Módulo Secretaria: entidade `Detalhamento`, ligando um `Lancamento` a uma ou mais inscrições
  (Encontreiro/Encontrista) ou outra origem (oferta, etc.), com CRUD completo e novo indicador
  `auditado` em Encontreiro/Encontrista
- Serviço de auditoria automática (`POST /detalhamentos/auditoria`) que casa inscrições pendentes de
  pagamento com lançamentos financeiros pela data/valor e interpreta a observação da inscrição para
  identificar pagamentos combinados (ex.: oferta ou outra inscrição paga no mesmo PIX). É executado
  automaticamente ao final de cada conciliação de Encontreiro/Encontrista

## [0.0.1] — 2026-07-18

### Adicionado
- Repositório extraído do monorepo `financeiro-encontro` como projeto independente
- API FastAPI para gestão financeira de eventos: autenticação JWT, CRUD de lançamentos (receita/despesa) e finalidades
- Conciliação de extratos bancários via importação de CSV (parser dedicado ao Banco Inter) com deduplicação por hash
- Endpoints de dashboard (totais, por dia, por mês, por finalidade) e relatórios (livro-caixa, resumo-geral)
- Controle de acesso por perfil de usuário
- Migrations via Alembic e seeds idempotentes para dados iniciais
