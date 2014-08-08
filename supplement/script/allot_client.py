#!/usr/bin/env python
# encoding: utf-8


from models.impression_master import ImpressionMasterModel
from models.client_master import ClientMasterModel
from models.campaign_client import CampaignClientModel
from script.cal_impression import CalculatorScript
from script import BaseScript
import random


class AllotClientScript(BaseScript):
    client_rate = CalculatorScript.client_rate

    def __init__(self, impression_master_id=None):
        super(AllotClientScript, self).__init__()
        self.im_id = impression_master_id
        if self.im_id:
            self.im = self.get_impression_master_by_id(self.im_id)

        self.total_client = self.count

    def run(self, impression_master_id=None):
        if impression_master_id:
            self.im_id = impression_master_id
            self.im = self.get_impression_master_by_id(self.im_id)

        if not self.im:
            self.logger.warning("[AllotClientScript]: no impression_master")
            return None

        clients_plan_num = self.im.total_client - self.count_plan
        if clients_plan_num > self.total_client:
            self.logger.error("[AllotClientScript]: clients is not enough.")
            return

        while clients_plan_num > 0:
            client = self.get_client_random()
            if self.is_exist_client_in_alloted(client.id):
                continue

            CampaignClientModel(impression_master_id=self.im_id,
                                client_id=client.id).save()
            self.logger.debug(client.id)
            clients_plan_num -= 1

    def is_exist_client_in_alloted(self, client_id):
        client = None
        try:
            client = CampaignClientModel.get(CampaignClientModel.impression_master_id == self.im_id,
                                             CampaignClientModel.client_id == client_id)
        except Exception as e:
            # self.logger.warning(e)
            pass

        return bool(client)

    def get_impression_master_by_id(self, id):
        try:
            im = ImpressionMasterModel.get(ImpressionMasterModel.id == id)
            return im
        except Exception as e:
            self.logger.warning(e)
            return None

    def get_client_random(self):
        id = random.randint(0, self.count - 1)
        client = self.get_client_by_id(id)
        return client

    def get_client_by_id(self, id):
        try:
            client = ClientMasterModel.get(ClientMasterModel.id == id)
        except Exception as e:
            self.logger.warning(e)
            client = None
        return client

    @property
    def count(self):
        clients = ClientMasterModel.select()
        return clients.count()

    @property
    def count_plan(self):
        """
        已经分配了的总的 client 数
        """
        clients = CampaignClientModel.select().where(
            CampaignClientModel.impression_master_id == self.im_id)
        return clients.count()
