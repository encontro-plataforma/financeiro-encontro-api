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

# cria venv se não existir
if [ ! -d "venv" ]; then
  echo "Criando ambiente virtual..."
  python -m venv venv
fi

echo "### Ativando ambiente virtual..."
source venv/Scripts/activate

echo "### Instalando dependências..."
pip install -r requirements.txt

echo "### Subindo servidor FastAPI na porta $APP_PORT..."
uvicorn app.main:app --reload --host 0.0.0.0 --port "$APP_PORT"
