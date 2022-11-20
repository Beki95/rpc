import asyncio  # noqa
import json
import logging
import uuid
from asyncio import AbstractEventLoop
from typing import (
    Any,
    MutableMapping,
)

import aio_pika
from aio_pika import (
    Channel,
    Message,
)
from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractRobustChannel,
    AbstractRobustConnection,
)
from aio_pika.patterns import JsonRPC
from aio_pika.pool import Pool

from remote_procedure.rabbitmq.protocols import RPCClientProtocol
from remote_procedure.rabbitmq.type import UnionRpc

LOGGER = logging.getLogger(__name__)


class RPCClient(RPCClientProtocol):

    def __init__(
            self,
            url: str,
            rpc: UnionRpc = JsonRPC,
    ):
        self.url = url
        self.RPC = rpc
        self.loop: AbstractEventLoop | None = None
        self.futures: MutableMapping[str, asyncio.Future] = {}
        self.connection_pool: Pool = Pool(
            self.connection_factory,
            max_size=2,
            loop=self.loop,
        )
        self.channel_pool: Pool = Pool(
            self.get_channel,
            max_size=10,
            loop=self.loop,
        )

    def set_event_loop(self, loop):
        self.loop = loop

    async def connection_factory(self, **kwargs) -> AbstractRobustConnection:
        LOGGER.info('Start rpc connection!!!')
        return await aio_pika.connect_robust(url=self.url, loop=self.loop)

    async def get_channel(self) -> AbstractRobustChannel:
        async with self.connection_pool.acquire() as connection:
            return await connection.channel()

    @classmethod
    def convert_message_to_dict(cls, message: bytes):
        try:
            return json.loads(message)
        except json.JSONDecodeError as error:
            LOGGER.error(msg=error.msg)
            return dict(
                error=True, msg='Message decode error!',
            )

    def on_response(self, message: AbstractIncomingMessage) -> None:
        if message.correlation_id is None:
            LOGGER.info(f"Bad message {message!r}")
            return
        future: asyncio.Future = self.futures.pop(message.correlation_id)
        resp: dict = self.convert_message_to_dict(message=message.body)
        future.set_result(resp)

    @classmethod
    def get_correlation_id(cls):
        return uuid.uuid4().__str__()

    async def publish(self, body: Any, queue_name):
        """https://aio-pika.readthedocs.io/en/latest/rabbitmq-tutorial/6-rpc.html#"""
        async with self.channel_pool.acquire() as channel:  # type: Channel
            result = await channel.declare_queue(exclusive=True)
            await result.consume(self.on_response)

            correlation_id = self.get_correlation_id()
            future = self.loop.create_future()
            self.futures[correlation_id] = future

            await channel.default_exchange.publish(
                message=Message(
                    body=body,
                    content_type='application/json',
                    correlation_id=correlation_id,
                    reply_to=result.name,
                ),
                routing_key=queue_name,
            )
            return await future
