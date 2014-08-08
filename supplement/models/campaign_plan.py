#!/usr/bin/env python
# encoding: utf-8


from peewee import DateTimeField, IntegerField
from models.base import BaseModel
from models.client_master import ClientMasterModel
from lib import logger


class CampaignPlanModel(BaseModel):

    id = IntegerField(primary_key=True)
    impression_master_id = IntegerField()
    client_master_id = IntegerField()
    campaign_date = DateTimeField()

    def __repr__(self):
        return "<CampaignPlanModel: %r>" % self.id

    class Meta:
        db_table = "bl_campaign_plan"

    def client(self):
        try:
            c = ClientMasterModel.get(ClientMasterModel.id==self.client_master_id)
            return c
        except Exception as e:
            logger.warning(e)
            return None
