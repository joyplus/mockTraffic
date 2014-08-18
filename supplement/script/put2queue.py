#!/usr/bin/env python
# encoding: utf-8


from script import BaseScript
from models.client_master import ClientMasterModel
from models.campaign_plan import CampaignPlanModel
from lib import get_campaign_plan_queue, config
import json


class PutToQueue(BaseScript):

    def __init__(self, impression_master_id=None):
        super(PutToQueue, self).__init__()

        self.im_id = impression_master_id

        if self.im_id:
            pass
        else:
            self.campaign_paln = None

    def run(self, impression_master_id=None):
        if not impression_master_id and not self.im_id:
            self.logger.warning("[PutToQueue]: no impression_master_id")
            return None

        self.im_id = impression_master_id
        self.campaign_paln_queue = get_campaign_plan_queue(self.im_id)
        self.campaign_paln_queue.use(config.get("tubes", "campaign_plan") + "_%s" % self.im_id)

        # 异常处理，如果队列里有则清空队列
        job = self.campaign_paln_queue.reserve(timeout=0)
        while job:
            job.delete()
            job = self.campaign_paln_queue.reserve(timeout=0)
        # 清空完毕，继续进行

        plans = self.get_campaign_plan(impression_master_id)
        for plan in plans:
            value = dict(id=plan.id,  # client_id
                         campaign_date=self.datetime2str(plan.campaign_date),
                         mac=plan.mac,
                         mac_md5=plan.mac_md5,
                         ip=plan.ip,
                         # targeting_code=plan.province_code,
                         # device_id=plan.device_id,
                         plan_id=plan.plan_id,
                         )
            value = self.json_dumps(value)
            self.logger.debug(value)
            self.campaign_paln_queue.put(value)


    def datetime2str(self, value):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    def json_dumps(self, value):
        return json.dumps(value)

    def get_campaign_plan(self, id):
        sql = """
        select t1.campaign_date, t1.id as plan_id, t2.* from `bl_campaign_plan`\
        as t1 left join `bl_client_master` as t2\
        on t2.id = t1.client_master_id
        where t1.impression_master_id = {im_id} order by t1.campaign_date
        """
        plans = CampaignPlanModel.raw(sql.format(im_id=id))
        return plans.execute()
