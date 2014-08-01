# coding: utf-8


from lib import logger

class BaseScript(object):

    def __init__(self):
        self.logger = logger

    def run(self):
        raise NotImplementedError
