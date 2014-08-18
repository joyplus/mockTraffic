#!/usr/bin/env python
# encoding: utf-8


from script import BaseScript
from models.campaign_done import CampaignDoneModel
import json
from lib import get_queue, config
import datetime


class GetResultScript(BaseScript):

    def __init__(self, impression_master_id=None):
        super(GetResultScript, self).__init__()

        self.im_id = impression_master_id


    def run(self, impression_master_id=None):
        if impression_master_id:
            self.im_id = impression_master_id

        self.result_queue = get_queue()
        self.result_queue.watch(
            config.get("tubes", "campaign_plan_result") + "_%s" % self.im_id)

        if not self.im_id:
            self.logger.warning("[GetResultScript]: no impression_master")
            return None

        job = self.result_queue.reserve()
        while job:
            value = self.json_loads(job.body)
            CampaignDoneModel(campaign_plan_id=value["id"],
                              finished_time=self.str2datetime(value["finished_time"]),
                              finished_status=1).save()
            job.delete()
            job = self.result_queue.reserve()

    def json_loads(self, value):
        return json.loads(value)

    def str2datetime(self, value):
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
