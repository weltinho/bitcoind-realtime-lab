import asyncio
import contextlib
from typing import Any

import zmq
import zmq.asyncio
from fastapi import WebSocket

from app.settings import settings


class ZmqEventRelay:
    def __init__(self) -> None:
        # Contexto asyncio do ZMQ (integra com loop async do FastAPI/Uvicorn).
        self._context = zmq.asyncio.Context()
        # Socket SUB (subscriber) para ouvir tópicos do bitcoind.
        self._socket: zmq.asyncio.Socket | None = None
        # Task de background que fica lendo frames do ZMQ.
        self._task: asyncio.Task[None] | None = None
        # Conjunto de clientes WebSocket conectados para broadcast.
        self._clients: set[WebSocket] = set()
        # Lock evita condição de corrida ao adicionar/remover clientes.
        self._clients_lock = asyncio.Lock()

    async def start(self) -> None:
        # Evita iniciar duas vezes e respeita feature flag.
        if self._task or not settings.zmq_enabled:
            return

        # Cria socket subscriber (SUB) e conecta nos endpoints de blocos e tx.
        socket = self._context.socket(zmq.SUB)
        socket.connect(settings.bitcoin_zmq_block)
        socket.connect(settings.bitcoin_zmq_tx)
        # Assina cada tópico configurado (ex: hashblock, hashtx).
        for topic in settings.bitcoin_zmq_topics:
            socket.setsockopt(zmq.SUBSCRIBE, topic.encode("ascii"))

        self._socket = socket
        # Inicia loop de leitura assíncrono sem bloquear startup da API.
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        # Cancela task de consumo do ZMQ com tratamento de cancelamento esperado.
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        # Fecha socket imediatamente (linger=0 evita esperar flush pendente).
        if self._socket:
            self._socket.close(linger=0)
            self._socket = None

        # Copia clientes atuais e limpa estrutura protegida por lock.
        async with self._clients_lock:
            clients = list(self._clients)
            self._clients.clear()

        # Fecha conexões WebSocket abertas sem derrubar shutdown em erro pontual.
        for client in clients:
            with contextlib.suppress(Exception):
                await client.close()

        # Libera contexto ZMQ.
        self._context.term()

    async def add_client(self, websocket: WebSocket) -> None:
        # Registra cliente para receber eventos de broadcast.
        async with self._clients_lock:
            self._clients.add(websocket)

    async def remove_client(self, websocket: WebSocket) -> None:
        # Remove cliente de forma segura; discard não falha se já não existir.
        async with self._clients_lock:
            self._clients.discard(websocket)

    async def _run(self) -> None:
        # Sem socket ativo, não há o que consumir.
        if not self._socket:
            return

        # Loop infinito de consumo dos frames multipart do ZMQ.
        while True:
            frames = await self._socket.recv_multipart()
            event = self._to_event(frames)
            await self._broadcast(event)

    @staticmethod
    def _to_event(frames: list[bytes]) -> dict[str, Any]:
        # Frame 0: tópico (ascii), frame 1: payload binário, frame 2: sequência.
        topic = frames[0].decode("ascii")
        # Serializa payload para hex por ser amigável para JSON.
        payload = frames[1].hex() if len(frames) > 1 else None
        # Sequência costuma vir em little-endian no publisher do bitcoind.
        sequence = (
            int.from_bytes(frames[2], byteorder="little") if len(frames) > 2 else None
        )
        return {"topic": topic, "payload_hex": payload, "sequence": sequence}

    async def _broadcast(self, event: dict[str, Any]) -> None:
        # Snapshot para não segurar lock durante I/O de rede.
        async with self._clients_lock:
            clients = list(self._clients)

        # Sem clientes conectados, ignora evento silenciosamente.
        if not clients:
            return

        # Guarda clientes que falharem no send para limpeza posterior.
        stale_clients: list[WebSocket] = []
        for client in clients:
            try:
                await client.send_json(event)
            except Exception:
                # Cliente desconectado/instável: marca para remoção.
                stale_clients.append(client)

        if not stale_clients:
            return

        # Remove conexões quebradas para não tentar enviar novamente.
        async with self._clients_lock:
            for client in stale_clients:
                self._clients.discard(client)
