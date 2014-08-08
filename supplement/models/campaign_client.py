#!/usr/bin/env python
# encoding: utf-8


from peewee import IntegerField
from models.base import BaseModel


class CampaignClientModel(BaseModel):

    id = IntegerField(primary_key=True)
    day_impression_id = IntegerField()
    client_id = IntegerField()
    impression_fre = IntegerField()
    actual_fre = IntegerField()

    def __repr__(self):
        return "<CampaignClientModel: %r>" % self.id

    class Meta:
        db_table = "bl_campaign_client"
