import json  # noqa
import logging
import uuid
from asyncio import AbstractEventLoop
from typing import (
    Any,
    Union,
)

import aio_pika
from aio_pika.abc import (
    AbstractRobustChannel,
    AbstractRobustConnection,
    TimeoutType,
)
from aio_pika.patterns import JsonRPC
from aio_pika.pool import Pool
from pika import (
    BlockingConnection,
    ConnectionParameters,
    PlainCredentials,
    URLParameters,
)
from pika.adapters.blocking_connection import (
    BlockingChannel,
)

from remote_procedure.rabbitmq.type import UnionRpc

LOGGER = logging.getLogger(__name__)


def get_correlation_id() -> str:  # UUID
    return uuid.uuid4().__str__()


class Connector:

    def __init__(
            self,
            url: Union[str, None] = None,
            heartbeat: int = 60,  # In seconds
            host: str = 'localhost',
            port: int = 5672,
            username: str = "guest",
            passwd: str = "guest",
            auto_delete: bool = True,
            durable: bool = False,
            exchange: str = '',
            prefetch_count: int = 1,
            connection_attempts: int = 2,
            retry_delay: int = 2,
            **kwargs,
    ):
        self.auto_delete = auto_delete
        self._exchange = exchange
        self.durable = durable
        self.prefetch_count = prefetch_count
        self.connection_attempts = connection_attempts
        self.retry_delay = retry_delay
        if url:
            self._conn_parameters = URLParameters(url=url)
        elif url is None:
            self._conn_parameters = ConnectionParameters(
                host=host,
                port=port,
                credentials=PlainCredentials(
                    username=username, password=passwd,
                ),
                heartbeat=heartbeat,
                connection_attempts=connection_attempts,
                retry_delay=retry_delay,
            )
        self._connection: BlockingConnection = self.connection_factory()

    def connection_factory(self) -> BlockingConnection:
        LOGGER.info('Start BlockingConnection')
        self._connection = BlockingConnection(parameters=self._conn_parameters)

        return self._connection

    def open_channel(self):
        channel = self._connection.channel()
        LOGGER.info(f'Open channel number: {channel.channel_number}')
        channel.basic_qos(prefetch_count=self.prefetch_count)

        if self._exchange:
            self.setup_exchange(self._exchange, channel=channel)
        return channel

    def setup_exchange(self, exchange, channel: BlockingChannel):
        channel.exchange_declare(
            exchange=exchange,
            auto_delete=self.auto_delete,
            durable=self.durable,
        )

    def setup_queue_declare(self, queue, channel: BlockingChannel):  # noqa
        return channel.queue_declare(
            queue=queue,
            exclusive=True,
        )

    def close_channel(self, channel: BlockingChannel):  # noqa
        LOGGER.info(f'Channel number: {channel.channel_number} closure')
        channel.close()


class AsyncConnector:

    def __init__(
            self,
            url: str,
            timeout: TimeoutType = None,
            rpc: UnionRpc = JsonRPC,
    ):
        self.url = url
        self.RPC = rpc
        self.loop: Union[AbstractEventLoop, None] = None
        self.timeout = timeout
        self.connection_pool: Pool = Pool(
            self.connection_factory,  # type: AbstractRobustConnection
            max_size=2,
            loop=self.loop,
        )
        self.channel_pool: Pool = Pool(
            self.get_channel,  # type: AbstractRobustChannel
            max_size=10,
            loop=self.loop,
        )

    def set_event_loop(self, loop):
        self.loop = loop

    async def get_channel(self) -> AbstractRobustChannel:
        async with self.connection_pool.acquire() as connection:
            return await connection.channel()

    async def connection_factory(self, **kwargs) -> AbstractRobustConnection:
        LOGGER.info('Start rpc connection!!!')
        return await aio_pika.connect_robust(
            url=self.url, loop=self.loop, timeout=self.timeout,
        )


class MessageConverter:
    SERIALIZER: json = json

    def convert_message_to_dict(self, message: bytes):
        try:
            return self.SERIALIZER.loads(message)
        except self.SERIALIZER.JSONDecodeError as error:
            LOGGER.error(msg=error.msg)
            return dict(
                error=True, msg='Message decode error!',
            )

    def convert_dict_to_bytes(self, obj: Any):
        return self.SERIALIZER.dumps(obj=obj).encode()
