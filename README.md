# bitcoin-coder

Learning project for Bitcoin Core RPC + ZMQ interactions with:

- `bitcoind` via official `bitcoincore/bitcoin` Docker image (arm64 compatible)
- Python web backend (FastAPI over ASGI, production-ready structure)
- Optional React frontend for visual exploration

## Project layout

- `docker-compose.yml`: local stack definition
- `infra/bitcoin/bitcoin.conf`: regtest-focused node config (RPC + ZMQ)
- `backend/`: Python API service
- `frontend/`: placeholder for future React app

## Quick start

1. Copy env template:

```bash
cp .env.example .env
```

2. Start Bitcoin Core:

```bash
docker compose up -d bitcoind
```

3. Start backend:

```bash
docker compose up --build backend
```

4. Start frontend + HTTPS gateway:

```bash
docker compose up --build frontend caddy
```

5. Check API:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/rpc/getblockchaininfo
```

6. Open UI:

```bash
https://localhost
```

## HTTPS notes (local)

- O gateway Caddy termina TLS localmente e faz proxy para frontend/backend.
- No primeiro acesso, o navegador pode avisar sobre certificado local (CA interna do Caddy).
- Para uso didático local isso é esperado; para produção, use domínio real com certificado público.

## Tests

Run backend tests locally:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

## Notes

- Uses `regtest` for safe local experimentation.
- `txindex=1` is enabled to make exploration easier.
- ZMQ endpoints are exposed over the Docker network for backend subscription work.
