import queue
from typing import (
    Any,
    Callable,
    TypeVar,
)

from remote_procedure.rabbitmq.protocols import PoolProtocol

T = TypeVar("T")
ObjectType = Callable[..., Any]


class PoolCtx(PoolProtocol):  # Sync pool
    __slots__ = 'max_size', '_callable', '__queue', 'item'

    def __init__(self, _callable: ObjectType, max_size: int = 10):
        self.max_size = max_size
        self._callable = _callable
        self.__queue = queue.Queue(maxsize=max_size)
        self.item: T = None  # Used object
        self.filling_the_pool()

    def filling_the_pool(self):
        for _ in range(self.max_size):
            obj = self._callable()
            self.__queue.put(obj)  # Add object in queue

    def acquire(self):
        if self.__queue.qsize() <= 0:
            raise ValueError('No more objects are available')
        self.item = self.__queue.get()
        return self.item

    def realise(self):
        if self.item:
            self.__queue.put(self.item)

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.realise()
