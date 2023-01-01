import logging  # noqa
from asyncio import AbstractEventLoop
from typing import (
    Any,
    Callable,
    Union,
)

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractRobustConnection,
)
from aio_pika.patterns import RPC
from pika import (
    BasicProperties,
    BlockingConnection,
)
from pika.adapters.blocking_connection import BlockingChannel

from remote_procedure.rabbitmq.base import (
    Connector,
    MessageConverter,
)
from remote_procedure.rabbitmq.protocols import (
    RPCAsyncServerProtocol,
    RPCSyncServerProtocol,
)
from remote_procedure.rabbitmq.type import (
    JsonRPC,
    UnionRpc,
)
from remote_procedure.router import (
    RPCRouter,
    RPCRouterProtocol,
)

LOGGER = logging.getLogger(__name__)


class RPCAsyncServer(RPCAsyncServerProtocol):

    def __init__(
            self,
            url,
            rpc: UnionRpc = JsonRPC,
    ):
        self.url = url
        self.RPC = rpc
        self.loop: Union[AbstractEventLoop, None] = None
        self.router: RPCRouterProtocol = RPCRouter()

    def include_router(self, router, *, prefix: str = '') -> None:
        self.router.include_route(router, prefix=prefix)

    async def connection(self) -> AbstractRobustConnection:
        return await aio_pika.connect_robust(
            url=self.url, loop=self.loop,
        )

    async def launch(self) -> RPC:
        robust_conn: AbstractRobustConnection = await self.connection()
        # Creating channel
        channel: AbstractChannel = await robust_conn.channel()
        # Creating RPC
        rpc = await self.RPC.create(channel)

        # Register and consume router
        for route in self.router.routes:  # noqa
            await rpc.register(
                route['path'].lstrip('_'),
                route['endpoint'],
                **route['kwargs'],
            )
        return rpc


class RPCSyncServer(RPCSyncServerProtocol, Connector, MessageConverter):

    def __init__(self, *args, **kwargs):
        self.router: RPCRouterProtocol = RPCRouter()
        self.consumer_tags: dict = {}
        self.routes: dict[..., Any] = {}
        self._channel: BlockingChannel
        super().__init__(*args, **kwargs)

    @classmethod
    def call_func(cls, func: Callable[..., Any], payload):
        if isinstance(payload, dict):
            return func(**payload)
        return func(payload)

    def on_call_message(self, ch, method, props, body):
        if method.routing_key not in self.routes:  # noqa
            LOGGER.warning("Method %r not registered in %r", method, self)
            return

        try:
            payload = self.convert_message_to_dict(message=body)

            func = self.routes[method.routing_key]  # noqa

            result = self.call_func(func=func, payload=payload)
        except Exception as exc:
            LOGGER.error(exc)

        result_message = self.convert_dict_to_bytes(result)  # noqa

        try:
            ch.basic_publish(
                exchange=method.exchange,
                routing_key=props.reply_to,
                properties=BasicProperties(
                    correlation_id=props.correlation_id,
                ),
                body=result_message,
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:  # noqa
            LOGGER.exception("Failed to send reply %r", result_message)
            return

    def start_consuming(self):  # noqa
        LOGGER.info(
            f'Channel number: {self._channel.channel_number} start consuming'
        )
        self._channel.start_consuming()

    def register(
            self,
            *,
            method_name,
            func: Callable[..., Any],
            **kwargs,
    ):
        if func in self.consumer_tags:
            raise RuntimeError("Function already registered")

        if method_name in self.router.routes:  # noqa
            raise RuntimeError(
                "Method name already used for %r" % self.router.routes[  # noqa
                    method_name,
                ],
            )
        kwargs.pop('timeout')
        self._channel.queue_declare(method_name, **kwargs)

        self.consumer_tags[func] = self._channel.basic_consume(
            on_message_callback=self.on_call_message, queue=method_name,
        )
        self.routes[method_name] = func  # noqa

    def include_router(self, router, *, prefix: str = '') -> None:
        self.router.include_route(router, prefix=prefix)

    def launch(self):
        self.connection_factory()  # type: BlockingConnection
        self._channel = self.open_channel()  # noqa

        for route in self.router.routes:  # noqa
            self.register(
                method_name=route['path'].lstrip('_'),
                func=route['endpoint'],
                **route['kwargs'],
            )
        self.start_consuming()
