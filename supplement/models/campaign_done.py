#!/usr/bin/env python
# encoding: utf-8


from peewee import DateTimeField, IntegerField
from models.base import BaseModel


class CampaignDoneModel(BaseModel):

    id = IntegerField(primary_key=True)
    campaign_plan_id = IntegerField()
    finished_time = DateTimeField()
    finished_status = IntegerField()

    def __repr__(self):
        return "<CampaignDoneModel: %r>" % self.id

    class Meta:
        db_table = "bl_campaign_master"
