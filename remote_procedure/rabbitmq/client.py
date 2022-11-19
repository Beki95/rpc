import asyncio
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
from starlette.datastructures import State  # noqa

from rpc.rabbitmq.type import UnionRpc


class RPCClient:

    def __init__(
            self,
            url: str,
            state: State,
            rpc: UnionRpc = JsonRPC,
    ):
        self.url = url
        self.RPC = rpc
        self.state: State = state
        self.loop: AbstractEventLoop | None = None
        self.futures: MutableMapping[str, asyncio.Future] = {}
        self.channel_pool: Pool = Pool(
            self.get_channel,
            max_size=10,
            loop=self.loop,
        )
        self.connection_pool: Pool = Pool(
            self.connection_factory,
            max_size=2,
            loop=self.loop,
        )

    def set_event_loop(self, loop):
        self.loop = loop

    async def connection_factory(self, **kwargs) -> AbstractRobustConnection:
        return await aio_pika.connect_robust(url=self.url, loop=self.loop)

    async def get_channel(self) -> AbstractRobustChannel:
        async with self.connection_pool.acquire() as connection:
            return await connection.channel()

    @classmethod
    def on_response(cls, message: AbstractIncomingMessage) -> None:
        if message.correlation_id is None:
            print(f"Bad message {message!r}")
            return
        # future: asyncio.Future = self.futures.pop(message.correlation_id)
        # future.set_result(message.body)

    async def publish(self, body: Any, queue_name):
        async with self.channel_pool.acquire() as channel:  # type: Channel
            result = await channel.declare_queue(exclusive=True)
            await channel.default_exchange.publish(
                message=Message(
                    body=body,
                    content_type='application/json',
                    reply_to=result.name,
                ),
                routing_key=queue_name,
            )
            # correlation_id = str(uuid.uuid4())
            # future = self.loop.create_future()
            # self.futures[correlation_id] = future
