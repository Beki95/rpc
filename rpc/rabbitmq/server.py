from asyncio import AbstractEventLoop

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractRobustConnection,
)
from aio_pika.patterns import (
    JsonRPC,
    RPC,
)

from rpc.rabbitmq.type import UnionRpc
from rpc.router import RPCRouter


class RPCServer:

    def __init__(
            self,
            url,
            rpc: UnionRpc = JsonRPC,
    ):
        self.url = url
        self.RPC = rpc
        self.loop: AbstractEventLoop | None = None
        self.router = RPCRouter()

    def set_event_loop(self, loop):
        self.loop = loop

    def include_router(self, router, *, prefix: str = '') -> None:
        self.router.include_route(router, prefix=prefix)

    async def connection(self) -> AbstractRobustConnection:
        return await aio_pika.connect_robust(
            url=self.url, loop=self.loop,
        )

    async def execute(self) -> RPC:
        robust_conn: AbstractRobustConnection = await self.connection()
        # Creating channel
        channel: AbstractChannel = await robust_conn.channel()
        # Creating RPC
        rpc = await self.RPC.create(channel)

        # Register and consume router
        for route in self.router.routes:
            await rpc.register(
                route['path'].lstrip('_'),
                route['endpoint'],
                **route['kwargs'],
            )
        return rpc
