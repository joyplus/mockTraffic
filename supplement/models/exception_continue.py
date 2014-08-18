#!/usr/bin/env python
# encoding: utf-8


from peewee import CharField, IntegerField
from models.base import BaseModel


class ExceptionContinueModel(BaseModel):

    id = IntegerField(primary_key=True)
    day_impression_id = IntegerField()
    type = CharField()
    nums = IntegerField()
    targeting_code = CharField()
    hour = CharField()

    def __repr__(self):
        return "<ExceptionContinueModel: %r>" % self.id

    class Meta:
        db_table = "bl_exception_continue"
