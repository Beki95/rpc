import abc
from typing import Any

from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractRobustChannel,
    AbstractRobustConnection,
)
from aio_pika.patterns import RPC

from remote_procedure.rabbitmq.type import (
    JsonRPC,
    UnionRpc,
)


class RPCClientProtocol(abc.ABC):

    @abc.abstractmethod
    def __init__(self, url: str, rpc: UnionRpc = JsonRPC):  # noqa
        raise NotImplementedError

    @abc.abstractmethod
    def set_event_loop(self, loop):
        raise NotImplementedError

    @abc.abstractmethod
    async def connection_factory(self, **kwargs) -> AbstractRobustConnection:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_channel(self) -> AbstractRobustChannel:
        raise NotImplementedError

    @abc.abstractclassmethod
    def on_response(cls, message: AbstractIncomingMessage) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def publish(self, body: Any, queue_name):
        raise NotImplementedError


class RPCServerProtocol(abc.ABC):

    @abc.abstractmethod
    def __init__(self, url, rpc: UnionRpc = JsonRPC):  # noqa
        raise NotImplementedError

    @abc.abstractmethod
    def set_event_loop(self, loop):
        raise NotImplementedError

    @abc.abstractmethod
    def include_router(self, router, *, prefix: str = '') -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def connection(self) -> AbstractRobustConnection:
        raise NotImplementedError

    @abc.abstractmethod
    async def execute(self) -> RPC:
        raise NotImplementedError
