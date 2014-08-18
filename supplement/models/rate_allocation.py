#!/usr/bin/env python
# encoding: utf-8


from peewee import CharField, IntegerField, FloatField
from models.base import BaseModel


class RateAllocationModel(BaseModel):

    id = IntegerField(primary_key=True)
    impression_master_id = IntegerField()
    type = CharField()
    rate = FloatField()
    targeting_code = CharField()

    def __repr__(self):
        return "<RateAllocationModel: %r>" % self.id

    class Meta:
        db_table = "bl_rate_allocation"
