#!/usr/bin/env python
# encoding: utf-8

import ConfigParser
from peewee import MySQLDatabase
import logging
import beanstalkc
from logbook import Logger
from redis import StrictRedis as Redis

config = ConfigParser.ConfigParser()
config.readfp(open('config.ini'))


def db():

    _db = MySQLDatabase(database=config.get("database", "name"),
                        host=config.get("database", "host"),
                        port=config.getint("database", "port"),
                        user=config.get("database", "user"),
                        passwd=config.get("database", "pass"),
                        charset="utf8",
                        )
    _db.connect()
    return _db


def redis():

    _db = Redis(host=config.get("redis", "host"),
                port=config.getint("redis", "port"))
    return _db


# beanstalkc
def get_queue(tube=None):
    beanstalk = beanstalkc.Connection(host=config.get("beanstalkc", "host"),
                                      port=config.getint("beanstalkc", "port"))
    if tube:
        beanstalk.watch(tube)
    return beanstalk


def get_campaign_plan_queue(im_id):
    return get_queue(config.get("tubes", "campaign_plan") + "_%s" % im_id)


#logger = logging.getLogger("supplement")
#enable_pretty_logging(logger, config.get("log", "level"))
if config.getboolean("log", "sql_record"):

    logger_sql = logging.getLogger('peewee')
    logger_sql.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[SQL %(asctime)s]: %(message)s")
    handler.setFormatter(formatter)
    logger_sql.addHandler(handler)

logger = Logger("supplement")
