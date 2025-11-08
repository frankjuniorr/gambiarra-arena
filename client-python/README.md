# Gambiarra Client - Python

Cliente Python para Gambiarra LLM Club Arena Local.

## Instalação

```bash
# Instalar com pip
pip install -e .

# Ou com dependências de desenvolvimento
pip install -e ".[dev]"
```

## Uso

### Executar com Mock Runner (teste)

```bash
gambiarra-client \
  --url ws://localhost:3000/ws \
  --pin 123456 \
  --participant-id test-python-1 \
  --nickname "Python Test" \
  --runner mock
```

### Executar com Ollama

```bash
gambiarra-client \
  --url ws://localhost:3000/ws \
  --pin 123456 \
  --participant-id python-ollama-1 \
  --nickname "Python Ollama" \
  --runner ollama \
  --model llama3.1:8b \
  --ollama-url http://localhost:11434
```

### Executar com LM Studio

```bash
gambiarra-client \
  --url ws://localhost:3000/ws \
  --pin 123456 \
  --participant-id python-lmstudio-1 \
  --nickname "Python LM Studio" \
  --runner lmstudio \
  --model local-model \
  --lmstudio-url http://localhost:1234
```

## Opções

```
--url                WebSocket server URL (default: ws://localhost:3000/ws)
--pin                Session PIN (required)
--participant-id     Participant ID (required)
--nickname           Participant nickname (required)
--runner             Runner type: ollama, lmstudio, mock (default: ollama)
--model              Model name (default: llama3.1:8b)
--temperature        Temperature (default: 0.8)
--max-tokens         Max tokens (default: 400)
--ollama-url         Ollama API URL (default: http://localhost:11434)
--lmstudio-url       LM Studio API URL (default: http://localhost:1234)
```

## Desenvolvimento

### Estrutura do Projeto

```
client-python/
├── gambiarra_client/
│   ├── __init__.py
│   ├── cli.py              # CLI principal
│   ├── net/
│   │   ├── __init__.py
│   │   └── ws.py           # Cliente WebSocket
│   └── runners/
│       ├── __init__.py
│       ├── types.py        # Tipos base
│       ├── mock.py         # Runner de teste
│       ├── ollama.py       # Runner para Ollama
│       └── lmstudio.py     # Runner para LM Studio
├── pyproject.toml
└── README.md
```

### Executar em modo desenvolvimento

```bash
# Executar diretamente
python -m gambiarra_client.cli --help

# Ou
python gambiarra_client/cli.py --help
```

### Testes

```bash
pytest
```

### Formatação de código

```bash
# Formatar com black
black gambiarra_client/

# Verificar com ruff
ruff check gambiarra_client/
```

## Protocolo WebSocket

O cliente implementa o mesmo protocolo do cliente TypeScript:

### Mensagens Cliente → Servidor

1. **register**: Registro inicial
```json
{
  "type": "register",
  "participant_id": "string",
  "nickname": "string",
  "pin": "string",
  "runner": "string",
  "model": "string"
}
```

2. **token**: Envio de token
```json
{
  "type": "token",
  "round": 1,
  "participant_id": "string",
  "seq": 0,
  "content": "string"
}
```

3. **complete**: Conclusão da geração
```json
{
  "type": "complete",
  "round": 1,
  "participant_id": "string",
  "tokens": 100,
  "latency_ms_first_token": 150,
  "duration_ms": 5000,
  "model_info": {
    "name": "llama3.1:8b",
    "runner": "ollama"
  }
}
```

4. **error**: Erro durante geração
```json
{
  "type": "error",
  "round": 1,
  "participant_id": "string",
  "code": "GENERATION_FAILED",
  "message": "string"
}
```

### Mensagens Servidor → Cliente

1. **challenge**: Novo desafio
```json
{
  "type": "challenge",
  "session_id": "string",
  "round": 1,
  "prompt": "string",
  "max_tokens": 400,
  "temperature": 0.8,
  "deadline_ms": 30000,
  "seed": 42
}
```

2. **heartbeat**: Keepalive
```json
{
  "type": "heartbeat"
}
```

3. **registered**: Confirmação de registro
```json
{
  "type": "registered",
  "participant_id": "string"
}
```

## Equivalência com Cliente TypeScript

Este cliente Python é funcionalmente equivalente ao cliente TypeScript:

- ✅ Mesmo protocolo WebSocket
- ✅ Suporte para Ollama, LM Studio e Mock
- ✅ Reconexão automática com backoff exponencial
- ✅ Streaming de tokens em tempo real
- ✅ Métricas de latência e throughput
- ✅ Tratamento de erros
- ✅ Interface CLI similar

## Licença

MIT
