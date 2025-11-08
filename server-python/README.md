# Gambiarra LLM Club Server (Python)

Servidor Python para a arena de competições locais de LLMs, implementado com FastAPI, SQLAlchemy e WebSockets.

## Stack Tecnológico

- **FastAPI** - Web framework async moderno
- **SQLAlchemy 2.0** - ORM com suporte async
- **Alembic** - Migrations de banco de dados
- **Pydantic** - Validação de dados e schemas
- **aiosqlite** - Driver SQLite async
- **uvicorn** - Servidor ASGI de alta performance
- **passlib + bcrypt** - Hashing de PINs
- **slowapi** - Rate limiting

## Instalação

### Requisitos

- Python 3.9+
- pip ou uv

### Setup

```bash
# Clonar o repositório
cd server-python

# Criar ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Copiar e configurar variáveis de ambiente
cp .env.example .env

# Inicializar banco de dados
alembic upgrade head
```

## Desenvolvimento

### Rodar o servidor

```bash
# Modo desenvolvimento (hot reload)
python -m src.main

# Ou com uvicorn diretamente
uvicorn src.main:app --reload --host 0.0.0.0 --port 3000
```

### Migrations

```bash
# Criar nova migration (após alterar models)
alembic revision --autogenerate -m "descrição da mudança"

# Aplicar migrations
alembic upgrade head

# Reverter última migration
alembic downgrade -1
```

### Testes

```bash
# Instalar dependências de desenvolvimento
pip install -e ".[dev]"

# Rodar testes
pytest

# Com cobertura
pytest --cov=src
```

## Estrutura do Projeto

```
server-python/
├── src/
│   ├── main.py              # FastAPI app + startup
│   ├── config.py            # Configurações
│   ├── database.py          # SQLAlchemy setup
│   ├── models/              # SQLAlchemy models
│   │   ├── session.py
│   │   ├── participant.py
│   │   ├── round.py
│   │   ├── metrics.py
│   │   └── vote.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── websocket.py
│   │   └── http.py
│   ├── websocket/
│   │   └── hub.py           # WebSocket manager
│   ├── core/                # Business logic
│   │   ├── rounds.py
│   │   ├── votes.py
│   │   └── metrics.py
│   └── api/
│       └── routes.py        # HTTP endpoints
├── alembic/                 # Database migrations
├── tests/                   # Testes
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## API Endpoints

### Session

- `POST /session` - Criar nova sessão (retorna PIN)
- `GET /session` - Obter sessão ativa

### Rounds

- `POST /rounds` - Criar round
- `POST /rounds/start` - Iniciar round (envia challenge via WebSocket)
- `POST /rounds/stop` - Parar round
- `GET /rounds/current` - Obter round atual com tokens em tempo real

### Votes

- `POST /votes` - Votar em participante
- `POST /votes/close` - Fechar votação
- `GET /scoreboard` - Obter scoreboard do round atual

### Metrics

- `GET /metrics` - Métricas da sessão
- `GET /export.csv` - Exportar dados em CSV

### Participants

- `POST /participants/kick` - Remover participante

### WebSocket

- `WS /ws` - Conexão WebSocket para participantes e telão

## Protocolo WebSocket

### Client → Server

```json
// Registro
{
  "type": "register",
  "participant_id": "player-1",
  "nickname": "Alice",
  "pin": "123456",
  "runner": "ollama",
  "model": "llama3.1:8b"
}

// Token streaming
{
  "type": "token",
  "round": 0,
  "participant_id": "player-1",
  "seq": 0,
  "content": "Hello"
}

// Conclusão
{
  "type": "complete",
  "round": 0,
  "participant_id": "player-1",
  "tokens": 100,
  "latency_ms_first_token": 50,
  "duration_ms": 2000,
  "model_info": {"name": "llama3.1:8b", "runner": "ollama"}
}
```

### Server → Client

```json
// Challenge
{
  "type": "challenge",
  "session_id": "uuid",
  "round": 0,
  "prompt": "Write a haiku about AI",
  "max_tokens": 400,
  "temperature": 0.8,
  "deadline_ms": 90000,
  "seed": null
}

// Heartbeat (a cada 30s)
{
  "type": "heartbeat",
  "ts": 1234567890
}
```

## Variáveis de Ambiente

Ver `.env.example` para lista completa. Principais:

- `HOST` - Host do servidor (padrão: 0.0.0.0)
- `PORT` - Porta do servidor (padrão: 3000)
- `DATABASE_URL` - URL do banco SQLite
- `CORS_ORIGINS` - Origens permitidas para CORS
- `PIN_LENGTH` - Tamanho do PIN (padrão: 6)

## Diferenças do Servidor Node.js

- **Database**: Schema independente (não compatível com servidor Node.js)
- **Validation**: Pydantic em vez de Zod
- **ORM**: SQLAlchemy em vez de Prisma
- **Rate Limiting**: slowapi em vez de @fastify/rate-limit
- **Async**: asyncio nativo do Python

## Documentação da API

Com o servidor rodando, acesse:

- Swagger UI: http://localhost:3000/docs
- ReDoc: http://localhost:3000/redoc

## Produção

```bash
# Instalar apenas dependências de produção
pip install -r requirements.txt

# Rodar com Gunicorn + Uvicorn workers
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:3000

# Ou apenas uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 3000 --workers 4
```

## Licença

MIT
