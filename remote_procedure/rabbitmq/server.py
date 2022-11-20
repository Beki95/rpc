from asyncio import AbstractEventLoop

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractRobustConnection,
)
from aio_pika.patterns import (
    RPC,
)

from remote_procedure.rabbitmq.protocols import RPCServerProtocol
from remote_procedure.rabbitmq.type import (
    JsonRPC,
    UnionRpc,
)
from remote_procedure.router import (
    RPCRouter,
    RPCRouterProtocol,
)


class RPCServer(RPCServerProtocol):

    def __init__(
            self,
            url,
            rpc: UnionRpc = JsonRPC,
    ):
        self.url = url
        self.RPC = rpc
        self.loop: AbstractEventLoop | None = None
        self.router: RPCRouterProtocol = RPCRouter()

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
        for route in self.router.routes:  # noqa
            await rpc.register(
                route['path'].lstrip('_'),
                route['endpoint'],
                **route['kwargs'],
            )
        return rpc
