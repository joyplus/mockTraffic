#!/usr/bin/env python
# encoding: utf-8


from script import BaseScript
import os.path
from lib import get_campaign_plan_queue, get_queue, config
from models.impression_master import ImpressionMasterModel
from models.campaign_plan import CampaignPlanModel
import json
import datetime
import urllib2
from urllib import urlencode
import re
import time
import random


class SendRequestScript(BaseScript):

    def __init__(self, impression_master_id=None):
        super(SendRequestScript, self).__init__()

        self.im_id = impression_master_id
        #self.campaign_paln_queue.use(config.get("tubes", "campaign_plan"))

        if self.im_id:
            pass
        else:
            self.campaign_paln = None

    def run(self, impression_master_id=None):
        self.im_id = impression_master_id
        self.campaign_paln_queue = get_campaign_plan_queue(self.im_id)
        self.im = self.get_impression_master_by_id(self.im_id)
        #self.result_queue = get_queue()
        #self.result_queue.use(
            #config.get("tubes", "campaign_plan_result") + "_%s" % self.im_id)

        if not self.im:
            self.logger.warning("[AllocationScript]: no impression_master")
            return None

        self.url1 = None

        def repl(matchobj):
            return "{" + matchobj.group(1) + "}"

        self.url1 = re.sub(r"%(\w+)%", repl, self.im.tracking_url_1)

        job = self.campaign_paln_queue.reserve(timeout=0)

        while job:
            value = self.json_loads(job.body)
            value["campaign_date"] = self.str2datetime(value["campaign_date"])
            now = datetime.datetime.now()
            now_hour = datetime.datetime(
                now.year, now.month, now.day, now.hour)
            # days 为正，将来的任务提前到现在，为负，执行以前的任务
            now_hour += datetime.timedelta(days=self.im.delay_days)
            value_now_hour = datetime.datetime(value["campaign_date"].year, value[
                "campaign_date"].month, value["campaign_date"].day, value["campaign_date"].hour)

            if now_hour > value_now_hour: # 清除这个小时未完成的任务
                job.delete()
                job = self.campaign_paln_queue.reserve(timeout=0)
                continue

            if now < value["campaign_date"]:
                self.logger.debug("wait") # , now, value["campaign_date"])
                continue

            url1, params = self.url1, value

            try:
                ts = time.time()
                ts -= random.randint(1500, 1800)

                url = url1.format(mac=params["mac_md5"], ip=params["ip"], ts=int(ts))
                if config.getboolean("log", "url_record"):
                    self.logger.info("[tracking url]:{url}".format(url=url))

                urllib2.urlopen(
                    url
                ).read()

                #CampaignPlanModel.raw(
                    #"UPDATE bl_campaign_plan set status=1 where id={id}".format(id=params["plan_id"])).\
                    #execute()

            except (urllib2.URLError, urllib2.HTTPError) as e:
                self.logger.error("send_request error, task: %r, exception: %r" % (params, e))

            self.logger.debug("worker work hard for %d" % params["plan_id"])

            job.delete()
            job = self.campaign_paln_queue.reserve(timeout=0)




    def get_time(self, value):
        year, month, day, hour, minute, second = value.year, value.month, value.day, value.hour, value.minute, value.second
        return dict(year=year, month=month, day=day, hour=hour, minute=minute, second=second)


    def str2datetime(self, value):

        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

    def datetime2str(self, value):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    def json_loads(self, value):
        return json.loads(value)

    def get_impression_master_by_id(self, id):
        try:
            im = ImpressionMasterModel.get(ImpressionMasterModel.id == id)
            return im
        except Exception as e:
            self.logger.warning(e)
            return None
