#!/usr/bin/env python
# encoding: utf-8

from lib import db
from peewee import Model

class BaseModel(Model):

    class Meta:
        database = db()
