import logging
import functools
from telethon.errors import RPCError

class IgnoreRPCErrors:
    logger: logging.Logger = None

    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func

    def __get__(self, obj, objtype=None):
        bound_f = functools.partial(self.__call__, obj)
        return bound_f
    
    @classmethod
    def set_logger(cls, logger):
        cls.logger = logger
    
    async def __call__(self, *args, **kwargs):
        try:
            value = await self.func(*args, **kwargs)
            return value
        except Exception as e:
            if isinstance(e, RPCError):
                self.__class__.logger.warning(f'Ignoring TL RPC error: {e}')
                return None
            raise e
