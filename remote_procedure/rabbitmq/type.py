from typing import Union

from aio_pika.patterns import (
    JsonRPC,
    RPC,
)

UnionRpc = Union[JsonRPC, RPC]
