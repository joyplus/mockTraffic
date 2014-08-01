#!/usr/bin/env python
# encoding: utf-8

import ConfigParser
from peewee import MySQLDatabase
import logging
from logger import enable_pretty_logging

config = ConfigParser.ConfigParser()
config.readfp(open('config.ini'))

db = MySQLDatabase(database=config.get("database", "name"),
                   host=config.get("database", "host"),
                   port=int(config.get("database", "port")),
                   user=config.get("database", "user"),
                   passwd=config.get("database", "pass"),
                   charset="utf8",
                   )
db.connect()

#logging.basicConfig(filename=config.get("log", "path"), format="[%(levelname)s %(asctime)s %(module)s:%(lineno)d]:%(message)s", level=logging.DEBUG)

logger = logging.getLogger("supplement")
enable_pretty_logging(logger, config.get("log", "level"))
