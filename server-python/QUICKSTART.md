# Guia de Início Rápido - Server Python

## Setup Rápido

```bash
# 1. Criar ambiente virtual
cd server-python
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou .\venv\Scripts\activate no Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar ambiente
cp .env.example .env

# 4. Inicializar banco de dados
alembic upgrade head

# 5. Popular com dados de teste (opcional)
python scripts/seed.py

# 6. Rodar servidor
python -m src.main
```

## Servidor rodando!

O servidor estará disponível em:
- API: http://localhost:3000
- Docs: http://localhost:3000/docs
- WebSocket: ws://localhost:3000/ws

## Testando a API

```bash
# Criar sessão (retorna PIN)
curl -X POST http://localhost:3000/session

# Obter sessão ativa
curl http://localhost:3000/session

# Criar round
curl -X POST http://localhost:3000/rounds \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID",
    "prompt": "Escreva um poema",
    "max_tokens": 400,
    "temperature": 0.8,
    "deadline_ms": 90000
  }'

# Iniciar round (envia challenge via WebSocket)
curl -X POST http://localhost:3000/rounds/start \
  -H "Content-Type: application/json" \
  -d '{"round_id": "ROUND_ID"}'

# Ver round atual com tokens em tempo real
curl http://localhost:3000/rounds/current

# Votar em participante
curl -X POST http://localhost:3000/votes \
  -H "Content-Type: application/json" \
  -d '{
    "round_id": "ROUND_ID",
    "participant_id": "PARTICIPANT_ID",
    "score": 5
  }'

# Ver scoreboard
curl http://localhost:3000/scoreboard

# Métricas da sessão
curl http://localhost:3000/metrics

# Exportar dados como CSV
curl http://localhost:3000/export.csv
```

## Conectando Cliente Python

```bash
cd ../client-python
pip install -r requirements.txt

gambiarra-client \
  --url ws://localhost:3000/ws \
  --pin 123456 \
  --participant-id test-1 \
  --nickname "Test User" \
  --runner ollama \
  --model llama3.1:8b
```

## Conectando Cliente TypeScript

```bash
cd ../client-typescript
pnpm install

pnpm dev -- \
  --url ws://localhost:3000/ws \
  --pin 123456 \
  --participant-id test-2 \
  --nickname "Test TS" \
  --runner ollama \
  --model llama3.1:8b
```

## Rodando Testes

```bash
# Instalar dependências de dev
pip install -e ".[dev]"

# Rodar testes
pytest

# Com cobertura
pytest --cov=src --cov-report=html
```

## Desenvolvimento

### Hot Reload

```bash
# O servidor já tem hot reload habilitado em modo development
python -m src.main

# Ou explicitamente com uvicorn
uvicorn src.main:app --reload
```

### Criar Migration

```bash
# Após alterar models em src/models/
alembic revision --autogenerate -m "descrição da mudança"

# Aplicar migration
alembic upgrade head
```

### Debug

```bash
# Ver logs detalhados
ENVIRONMENT=development python -m src.main
```

## Troubleshooting

### Erro: "No module named 'src'"

Certifique-se de estar no diretório `server-python` ao rodar comandos.

### Erro: "Database is locked"

SQLite não suporta múltiplas escritas simultâneas. Use apenas uma instância do servidor por vez, ou considere PostgreSQL para produção.

### Erro: "Address already in use"

Outra aplicação está usando a porta 3000. Altere `PORT` no `.env` ou pare o outro servidor.

### WebSocket não conecta

Verifique:
1. Servidor está rodando
2. URL está correta (ws:// não wss:// para desenvolvimento local)
3. Firewall não está bloqueando a porta

## Próximos Passos

1. ✅ Servidor rodando
2. ✅ Clientes conectando
3. ✅ Rounds criados e iniciados
4. ✅ Tokens sendo transmitidos
5. ✅ Votação funcionando
6. ✅ Scoreboard atualizado

Divirta-se competindo com LLMs locais! 🎮🤖
