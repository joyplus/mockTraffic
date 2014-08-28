#!/usr/bin/env python
# encoding: utf-8


from script import BaseScript
from models.client_master import ClientMasterModel
from models.campaign_plan import CampaignPlanModel
from models.day_impression import DayImpressionModel
from lib import get_campaign_plan_queue, config
import datetime
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

        days = DayImpressionModel.select().where(DayImpressionModel.impression_master_id == self.im_id)
        days_date = [day.date for day in days]
        days_date = sorted(days_date)
        for day in days_date:
            self.logger.info("put {day}".format(day=str(day)))
            plans = self.get_campaign_plan(impression_master_id, day, self.get_tomorrow(day))
            for plan in plans:
                value = dict(plan_id=plan.id,
                            campaign_date=self.datetime2str(plan.campaign_date),
                            mac_md5=plan.mac_md5,
                            ip=plan.ip,
                            )
                value = self.json_dumps(value)
                self.logger.debug(value)
                self.campaign_paln_queue.put(value)


    def datetime2str(self, value):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    def json_dumps(self, value):
        return json.dumps(value)

    def get_campaign_plan(self, id, date1, date2):
        sql = """
        select t1.campaign_date, t1.id, t2.mac_md5, t2.ip from `bl_campaign_plan`\
        as t1 left join `bl_client_masters` as t2\
        on t2.id = t1.client_master_id
        where t1.impression_master_id = {im_id} and
        t1.campaign_date >= '{date1}' and t1.campaign_date < '{date2}'
        order by t1.campaign_date
        """
        plans = CampaignPlanModel.raw(sql.format(im_id=id, date1=str(date1), date2=str(date2)))
        return plans.execute()

    def get_tomorrow(self, date):
        return date + datetime.timedelta(days=1)
