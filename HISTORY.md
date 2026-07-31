# Histórico de Versões

## [0.3.2] — 2026-07-31

### Corrigido
- `app/core/config.py` não carregava o `.env` sozinho — dependia do processo já ter as variáveis no
  ambiente (via `start-backend.sh`, que faz `source .env`, ou via `envFile` do VS Code). A config de debug
  "FastAPI: Debug backend" sobe o uvicorn direto via debugpy e, quando o `envFile` do VS Code não é aplicado
  corretamente, `DATABASE_URL` caía no fallback hardcoded errado, derrubando a app no startup por falha de
  autenticação no banco. `config.py` agora chama `load_dotenv()` (dependência `python-dotenv` já existia no
  `requirements.txt`, mas nunca era usada)
- `.vscode/launch.json`: removido `--reload` da config de debug — incompatibilidade conhecida entre o
  reloader do uvicorn e o debugpy no Windows (`KeyboardInterrupt` no processo filho durante o attach ao
  subprocesso recarregado)
- `BancoInterParser.parse`: corrigido "too many values to unpack" ao desestruturar a linha do CSV — a
  validação de tamanho da linha já exigia a coluna de saldo, mas ela não estava sendo capturada na
  desestruturação
- `EncontreiroRepository`/`EncontristaRepository`: soma dos Detalhamentos e status do Lancamento agora
  também são sincronizados quando o vínculo é criado pela auditoria automática em lote, não só pelos
  endpoints manuais (ver `AuditoriaService` abaixo)

### Adicionado
- Filtro `nome_pagador` em `GET /encontreiros` e `GET /encontristas` (`ilike`), usado pela busca por nome do
  pagador no dialog de vínculo de inscrição

### Alterado
- `DetalhamentoService.create`/`update` passam a forçar a finalidade do lançamento vinculado para
  "INSCRIÇÃO" sempre que o detalhamento é de inscrição (Encontreiro ou Encontrista) — cobre tanto a criação
  do vínculo quanto a troca do lançamento vinculado
- `AuditoriaService.processar()` passa a criar os Detalhamentos via `DetalhamentoService.create()` em vez de
  `db.add()` direto — os vínculos automáticos da auditoria em lote agora também sincronizam o status do
  lançamento e aplicam a finalidade "INSCRIÇÃO" acima

## [0.3.1] — 2026-07-26

### Corrigido
- `POST /detalhamentos` e `PUT /detalhamentos/{id}` passam a validar que a soma dos valores dos
  Detalhamentos vinculados a um lançamento não ultrapasse o valor desse lançamento — retorna 400 com a
  mensagem informando quanto ainda resta disponível. Cobre também o caminho de "trocar lançamento" do
  vínculo em Encontreiro/Encontrista (`VinculoLancamentoComponent.trocar`), que reatribui um Detalhamento
  existente a outro `lancamento_id`

## [0.3.0] — 2026-07-25

### Adicionado
- `PATCH /lancamentos/conciliar/{id}/finalidade/{finalidade_id}` passa a aceitar `detalhamento_final`
  (`{descricao}`) no corpo: quando o valor do lançamento é maior que a soma dos `Detalhamento`s já
  vinculados, cria automaticamente um Detalhamento de sobra (`OFERTA` ou `OUTRO`, conforme a finalidade)
  com esse valor, na mesma transação que concilia o lançamento
- `Lancamento` ganha os campos computados `quantidade_detalhamentos` e `soma_detalhamentos` (mesmo padrão
  do `auditado` em Encontreiro/Encontrista), expostos em `LancamentoResponse` para evitar N+1 chamadas ao
  montar a tela de conciliação

### Alterado
- Finalidades "INSCRIÇÃO ENCONTRISTA" (id 3) e "INSCRIÇÃO ENCONTREIRO" (id 4) unificadas em uma única
  finalidade "INSCRIÇÃO" (id 3) — migration atualiza os lançamentos existentes e remove o id 4
- `PATCH /lancamentos/conciliar/...` para lançamentos de RECEITA agora valida, antes de conciliar: (1) a
  soma dos Detalhamentos vinculados não pode ultrapassar o valor do lançamento; (2) se a finalidade for
  "INSCRIÇÃO", é obrigatório já existir ao menos um Detalhamento de inscrição (Encontreiro ou Encontrista)
  vinculado

## [0.2.1] — 2026-07-25

### Alterado
- Conciliação de extrato bancário (`POST /conciliacao/upload`) também passa a ser assíncrona
  (`BackgroundTasks`), no mesmo padrão da conciliação de Encontreiro/Encontrista: responde na hora com
  `{upload_id, status}` e processa em segundo plano, salvando o resumo em `resultado_processamento`

## [0.2.0] — 2026-07-25

### Corrigido
- Seed de `Círculo`: `rgb` passa a guardar códigos hexadecimais válidos (antes tinha nomes soltos do
  Google Sheets, incompatíveis com um seletor de cor nativo no frontend)

### Adicionado
- Conciliação de Encontreiro/Encontrista via CSV passa a ser assíncrona (`BackgroundTasks`): o endpoint
  responde na hora com o id do upload, o processamento roda em segundo plano, e o resumo final
  (`resultado_processamento`) fica salvo no `UploadFile` para consulta posterior. `GET /uploads/{id}`
  agora expõe `status` e `resultado_processamento`
- Novos filtros de listagem para Encontreiro (`nome_ou_apelido`, `equipe_ids`, `situacao_camisa`,
  `auditado`) e Encontrista (`nome_ou_apelido`, `circulo_ids` — com `0` = sem círculo —, `padrinho_id`,
  `auditado`); as respostas passam a embutir `equipe`/`circulo`/`padrinho`. Novo endpoint
  `GET /encontristas/padrinhos-disponiveis`

### Alterado
- `Detalhamento.observacao` renomeado para `descricao` (só usado em `OFERTA`/`OUTRO`). Para inscrições, a
  "observação" não é mais duplicada/sincronizada — `DetalhamentoResponse` ganha `detalhe_nome` e
  `observacao_efetiva`, calculados na hora a partir do Encontreiro/Encontrista referenciado.
  `GET /encontreiros/{id}` e `GET /encontristas/{id}` passam a expor `detalhamento_id` e
  `lancamento_vinculado`, para a tela poder ligar/trocar/remover o vínculo com um lançamento

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
