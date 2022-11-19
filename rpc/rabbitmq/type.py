from aio_pika.patterns import (
    JsonRPC,
    RPC,
)

UnionRpc = JsonRPC | RPC
