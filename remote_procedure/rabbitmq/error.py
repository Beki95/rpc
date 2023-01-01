class ChannelClosedByBrokerError(Exception):
    """Channel %s is closed or there is no such channel"""


class CouldNotReconnect(Exception):
    """Сouldn't reconnect to the amqp server"""
