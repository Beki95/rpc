import abc
from typing import (
    Any,
    Callable,
)

from aio_pika.abc import (
    AbstractIncomingMessage,
    TimeoutType,
)
from aio_pika.patterns import RPC
from pika.adapters.blocking_connection import BlockingChannel

from remote_procedure.rabbitmq.type import (
    JsonRPC,
    UnionRpc,
)


class RPCAsyncClientProtocol(abc.ABC):

    @abc.abstractmethod
    def __init__(self, url: str, rpc: UnionRpc = JsonRPC):  # noqa
        raise NotImplementedError

    @abc.abstractclassmethod
    def on_response(cls, message: AbstractIncomingMessage) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def rpc_call(self, body: Any, queue_name, timeout: TimeoutType):
        raise NotImplementedError


class RPCAsyncServerProtocol(abc.ABC):

    def set_event_loop(self, loop):
        self.loop = loop  # noqa

    @abc.abstractmethod
    def include_router(self, router, *, prefix: str = '') -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def launch(self) -> RPC:
        raise NotImplementedError


class RPCSyncClientProtocol(abc.ABC):
    @abc.abstractmethod
    def on_response(self, ch: BlockingChannel, method, props, body):
        raise NotImplementedError

    @abc.abstractmethod
    def consume(self, queue, channel: BlockingChannel):
        raise NotImplementedError

    @abc.abstractmethod
    def rpc_call(self, routing_key, body, timout: TimeoutType):
        raise NotImplementedError


class RPCSyncServerProtocol(abc.ABC):
    @abc.abstractmethod
    def include_router(self, router, *, prefix: str = '') -> None:
        raise NotImplementedError

    @abc.abstractclassmethod
    def call_func(cls, func: Callable[..., Any], payload):
        raise NotImplementedError

    @abc.abstractmethod
    def register(
            self,
            *,
            method_name,
            func: Callable[..., Any],
            **kwargs,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def on_call_message(self, ch, method, props, body):
        raise NotImplementedError

    @abc.abstractmethod
    def launch(self) -> None:
        raise NotImplementedError


class PoolProtocol(abc.ABC):

    @abc.abstractmethod
    def filling_the_pool(self):
        raise NotImplementedError

    @abc.abstractmethod
    def acquire(self):
        raise NotImplementedError

    @abc.abstractmethod
    def realise(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError
