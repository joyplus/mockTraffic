#!/usr/bin/env python
# encoding: utf-8

from peewee import CharField, IntegerField, DateField
from models.base import BaseModel


class ImpressionMasterModel(BaseModel):

    id = IntegerField(primary_key=True)
    tracking_url_1 = CharField()
    tracking_url_2 = CharField()
    tracking_url_3 = CharField()
    campaign_name = CharField()
    total_impression = IntegerField()
    total_client = IntegerField()
    start_date = DateField()
    end_date = DateField()
    total_actual_impression = IntegerField()
    total_actual_client = IntegerField()

    def __repr__(self):
        return "<ImpressionMasterModel: %r>" % self.id

    class Meta:
        db_table = "bl_impression_master"

    def get_impression_percent(self):
        if self.total_actual_impression:
            return float(self.total_actual_impression) / self.total_impression * 100
        return 0

    def get_client_percent(self):
        if self.total_actual_client:
            return float(self.total_actual_client) / self.total_client * 100
        return 0
