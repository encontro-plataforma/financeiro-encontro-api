#!/bin/bash

echo "======================================"
echo "Iniciando Backend - Financeiro Encontro"
echo "======================================"

# carrega .env se existir
if [ -f ".env" ]; then
  echo "### Carregando variáveis de ambiente do .env..."
  set -a
  source .env
  set +a
fi

APP_PORT=${APP_PORT:-8000}

echo "### Sincronizando dependências com uv..."
uv sync

echo "### Subindo servidor FastAPI na porta $APP_PORT..."
uv run fastapi dev app/main.py --host 0.0.0.0 --port "$APP_PORT"
