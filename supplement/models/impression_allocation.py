#!/usr/bin/env python
# encoding: utf-8


from peewee import IntegerField, DateTimeField
from models.base import BaseModel


class ImpressionAllocationModel(BaseModel):

    id = IntegerField(primary_key=True)
    rate_allocation_id = IntegerField()
    impression = IntegerField()
    client = IntegerField()
    campaign_date = DateTimeField()
    actual_impression = IntegerField()
    actual_client = IntegerField()
    finished_date = DateTimeField()

    def __repr__(self):
        return "<ImpressionAllocationModel: %r>" % self.id

    class Meta:
        db_table = "bl_impression_allocation"

    def get_impression_percent(self):
        if self.actual_impression:
            return float(self.actual_impression) / self.impression * 100
        return 0

    def get_client_percent(self):
        if self.actual_client:
            return float(self.actual_client) / self.client * 100
        return 0
