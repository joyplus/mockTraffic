#!/usr/bin/env python
# encoding: utf-8


from peewee import CharField, IntegerField, DateField
from models.base import BaseModel


class DayImpressionModel(BaseModel):

    id = IntegerField(primary_key=True)
    impression_master_id = IntegerField()
    date = DateField()
    impression = IntegerField()
    client = IntegerField()

    def __repr__(self):
        return "<DayImpressionModel: %r>" % self.id

    class Meta:
        db_table = "bl_day_impression"
