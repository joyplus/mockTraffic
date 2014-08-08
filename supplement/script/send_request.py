#!/usr/bin/env python
# encoding: utf-8


from script import BaseScript
from lib import get_campaign_plan_queue, get_queue, config
from models.impression_master import ImpressionMasterModel
import json
import datetime
import urllib2
from urllib import urlencode
import gevent
from gevent import monkey
from gevent.queue import Queue
monkey.patch_socket()


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
        self.result_queue = get_queue()
        self.result_queue.use(
            config.get("tubes", "campaign_plan_result") + "_%s" % self.im_id)

        if not self.im:
            self.logger.warning("[AllocationScript]: no impression_master")
            return None

        #self.boss()
        self.jobs_queue = Queue(maxsize=4)

        gevent.joinall([
            gevent.spawn(self.boss),
            gevent.spawn(self.worker),
            gevent.spawn(self.worker),
            gevent.spawn(self.worker),
            gevent.spawn(self.worker),
        ])


    def get_time(self, value):
        year, month, day, hour, minute, second = value.year, value.month, value.day, value.hour, value.minute, value.second
        return dict(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

    def boss(self):
        job = self.campaign_paln_queue.reserve(timeout=0)
        while job:
            value = self.json_loads(job.body)
            value["campaign_date"] = self.str2datetime(value["campaign_date"])
            #value_time = self.get_time(value["campaign_date"])
            #now = self.get_time(datetime.datetime.now())
            now = datetime.datetime.now()

            # 一小时之内的 paln 可以执行
            now_hour = datetime.datetime(now.year, now.month, now.day, now.hour)
            value_now_hour = datetime.datetime(value["campaign_date"].year, value[
                                          "campaign_date"].month, value["campaign_date"].day, value["campaign_date"].hour)
            if now_hour > value_now_hour:
                #print "wait", now, value["campaign_date"]
                #print "pass"
                job.delete()
                job = self.campaign_paln_queue.reserve(timeout=0)
                continue

            # TODO: 清除上个小时未执行完的任务

            if now < value["campaign_date"]:
                #print "wait", now, value["campaign_date"]
                self.logger.info("wait")#, now, value["campaign_date"])
                continue

            task = self.im.tracking_url_1, value
            self.jobs_queue.put(task)

            #result = self.worker(task)

            #self.result_queue.put(
                #json.dumps(dict(result=result, id=value["id"])))
            job.delete()
            job = self.campaign_paln_queue.reserve(timeout=0)


    def worker(self):
        task = self.jobs_queue.get() # block wait for a job
        while task:
            url, params = task
            #data = urlencode(params)
            #result = urllib2.urlopen(url ,data).read()
            result = urllib2.urlopen(url.format(mac=params["mac_md5"], ip=params["ip"])).read()

            now = datetime.datetime.now()
            self.result_queue.put(
                #json.dumps(dict(result=self.json_loads(result), id=params["id"])))
                json.dumps(dict(result=result,
                                id=params["plan_id"],
                                finished_time=self.datetime2str(now))))
            self.logger.debug("worker work hard for %d" % params["plan_id"])

            task = self.jobs_queue.get()
            #return urllib2.urlopen(url, data).read()

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
