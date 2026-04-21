# bitcoind-realtime-lab

Playground para **JSON-RPC** e **eventos ZMQ** (`hashblock`, `hashtx`) de um nó Bitcoin Core, com stack pronta em Docker.

- **`bitcoind`** em regtest, imagem [`bitcoin/bitcoin:31.0`](https://hub.docker.com/r/bitcoin/bitcoin) (multi-arquitetura).
- **Backend** Python (FastAPI): repasse de RPC para o nó e relay WebSocket dos eventos ZMQ.
- **Frontend** React + Vite: laboratório de chamadas RPC (GET/POST + params) e painel ao vivo do stream ZMQ.
- **Caddy**: HTTPS local (`tls internal`) e reverse proxy para `/api`, `/ws` e o app.

## Layout

- `docker-compose.yml`: bitcoind, backend, frontend, Caddy
- `infra/bitcoin/bitcoin.conf`: regtest, RPC, ZMQ (rede Docker)
- `infra/caddy/Caddyfile`: gateway HTTPS e roteamento
- `backend/`: API
- `frontend/`: UI didática

## Quick start

1. Copie o env de exemplo. **`BITCOIN_RPC_USER` / `BITCOIN_RPC_PASSWORD`** alimentam o **backend** e, pelo `docker-compose`, também o **bitcoind** (`-rpcuser` / `-rpcpassword`), para não haver 401 por credencial divergente.

```bash
cp .env.example .env
```

2. Suba tudo (ou só os serviços que precisar):

```bash
docker compose up -d --build
```

3. Saúde da API:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/rpc/getblockchaininfo
```

4. Abra a UI no navegador:

`https://localhost` (aceite o certificado local do Caddy na primeira vez).

## HTTPS (local)

O Caddy usa **CA interna**; o aviso do navegador é esperado em ambiente de estudo. Em produção, use **domínio público** e certificado válido (ex.: Let’s Encrypt).

## Testes (backend)

Dentro do container (como no dia a dia do projeto):

```bash
docker compose exec -T backend pip install -r requirements-dev.txt
docker compose exec -T backend sh -lc 'PYTHONPATH=/app pytest tests/'
```

## Notas

- Rede **regtest** para experimentação isolada.
- `txindex=1` no nó para consultas mais amplas.
- RPC e ZMQ do `bitcoind` ficam na **rede Docker**; o host expõe principalmente **80/443** (Caddy) e o que você mapear no compose (ex.: P2P regtest).
