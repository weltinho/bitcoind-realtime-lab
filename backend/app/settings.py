from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Permite variáveis extras no ambiente sem quebrar inicialização.
    model_config = SettingsConfigDict(extra="ignore")

    # Host base do bitcoind, compartilhado entre RPC e ZMQ.
    bitcoin_host: str = "bitcoind"
    # Credenciais e porta do JSON-RPC do bitcoind.
    bitcoin_rpc_user: str = "bitcoinrpc"
    bitcoin_rpc_password: str = "bitcoinrpcdevpassword"
    bitcoin_rpc_port: int = 18443
    # Rede usada (regtest/testnet/mainnet).
    bitcoin_network: str = "regtest"

    # Portas ZMQ publicadas pelo bitcoind.
    bitcoin_zmq_block_port: int = 28332
    bitcoin_zmq_tx_port: int = 28333
    # Tópicos assinados no socket SUB.
    bitcoin_zmq_topics: tuple[str, ...] = ("hashblock", "hashtx")
    # Chave de feature flag para ativar/desativar relay de eventos em tempo real.
    zmq_enabled: bool = True

    @property
    def rpc_url(self) -> str:
        # URL final usada pelo cliente HTTP JSON-RPC.
        return f"http://{self.bitcoin_host}:{self.bitcoin_rpc_port}"

    @property
    def bitcoin_zmq_block(self) -> str:
        # Endpoint ZMQ para publicação de novos blocos.
        return f"tcp://{self.bitcoin_host}:{self.bitcoin_zmq_block_port}"

    @property
    def bitcoin_zmq_tx(self) -> str:
        # Endpoint ZMQ para publicação de novas transações.
        return f"tcp://{self.bitcoin_host}:{self.bitcoin_zmq_tx_port}"


# Instância singleton carregada de env vars automaticamente.
settings = Settings()
