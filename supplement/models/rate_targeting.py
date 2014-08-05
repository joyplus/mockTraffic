#!/usr/bin/env python
# encoding: utf-8


from peewee import CharField, IntegerField
from models.base import BaseModel


class RateTargetingModel(BaseModel):

    id = IntegerField(primary_key=True)
    targeting_code = CharField()
    targeting_type = CharField()
    rate_name = CharField()

    def __repr__(self):
        return "<RateTargetingModel: %r>" % self.id

    class Meta:
        db_table = "bl_rate_targeting"
