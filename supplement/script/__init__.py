# coding: utf-8


from lib import logger, redis, config

class BaseScript(object):

    def __init__(self):
        self.logger = logger

    def run(self):
        raise NotImplementedError

    def exit_supervisor(self, code=11):
        exit(code)

    @property
    def redis(self):
        return redis()

    def wrapper_redis_key(self, key):
        return "{prefix}:{key}".format(prefix=config.get("redis", "prefix"),
                                       key=key)
