#!/usr/bin/env python
# encoding: utf-8


from models.client_master import ClientMasterModel
from models.impression_allocation import ImpressionAllocationModel
from models.day_impression import DayImpressionModel
from models.exception_continue import ExceptionContinueModel
from models.impression_master import ImpressionMasterModel
from models.rate_allocation import RateAllocationModel
from models.campaign_client import CampaignClientModel
from models.campaign_plan import CampaignPlanModel
from script import BaseScript
import random


class AllotPlanScript(BaseScript):

    def __init__(self, impression_master_id=None):
        super(AllotPlanScript, self).__init__()

        self.im_id = impression_master_id
        if self.im_id:
            self.im = self.get_impression_master_by_id(self.im_id)
            self.region_rate = self.get_region_allocation()
            self.clock_rate = self.get_clock_allocation()
            self.di = self.get_day_impression()
        else:
            self.im = None

    def run(self, impression_master_id=None):
        if impression_master_id:
            self.im_id = impression_master_id
            self.im = self.get_impression_master_by_id(impression_master_id)
            self.region_rate = self.get_region_allocation()
            self.clock_rate = self.get_clock_allocation()
            self.di = self.get_day_impression()

        if not self.im:
            self.logger.warning("[AllocationScript]: no impression_master")
            return None
        elif not self.region_rate or not self.clock_rate:
            self.logger.warning("[AllocationScript]: no rate_allocation")
        elif not self.di:
            self.logger.warning("[AllocationScript]: no day_impression")


        # 清除已经有的数据
        delete_exception = """
        delete from bl_campaign_plan
        where impression_master_id={impression_master_id}
        """
        CampaignPlanModel.raw(delete_exception.format(impression_master_id=self.im.id)).execute()

        for day in self.di:
            list_key = "campaign_client:{im_id}:{day_impression_id}".format(im_id=self.im_id,
                                                                                day_impression_id=day.id)
            value = self.redis.lpop(self.wrapper_redis_key(list_key))
            while value:
                key = "campaign_client:{id}:{day_impression_id}".format(id=value,
                                                                        day_impression_id=day.id)
                self.redis.delete(self.wrapper_redis_key(key))
                value = self.redis.lpop(self.wrapper_redis_key(list_key))


        # put to redis
        for day in self.di:
            clients = CampaignClientModel.select(CampaignClientModel.id,
                                                 CampaignClientModel.plan_impression,
                                                 CampaignClientModel.client_id).\
                where(CampaignClientModel.day_impression_id==day.id,
                      CampaignClientModel.plan_impression>0)
            self.logger.debug("start put clients {im_id}:{day_impression_id} to redis.".\
                              format(im_id=self.im_id, day_impression_id=day.id))

            for client in clients:

                pipe = self.redis.pipeline()
                value = dict(id=client.id,
                             client_id=client.client_id,
                             actual_plan_impression=client.plan_impression)

                key = "campaign_client:{id}:{day_impression_id}".format(id=client.id,
                                                                           day_impression_id=day.id)
                pipe.hmset(self.wrapper_redis_key(key), value)
                list_key = "campaign_client:{im_id}:{day_impression_id}".format(im_id=self.im_id,
                                                                                   day_impression_id=day.id)
                pipe.lpush(self.wrapper_redis_key(list_key), client.id)
                pipe.execute()

            self.logger.debug("end put clients {im_id}:{day_impression_id} to redis, total {nums}.".\
                              format(im_id=self.im_id,
                                     day_impression_id=day.id,
                                     nums=clients.count()))


        for day in self.di:
            impression = day.impression

            if impression <= 0:
                continue

            self.logger.debug("start day:{im_id}:{day_impression_id}.".\
                              format(im_id=self.im_id, day_impression_id=day.id))

            for hour in self.clock_rate:
                client_plan_nums = impression * hour.rate / 100; # 一小时的 client
                self.logger.debug("start hour:{hour}:{client_plan_nums}.".\
                                  format(im_id=self.im_id,
                                         day_impression_id=day.id,
                                         hour=hour.targeting_code,
                                         client_plan_nums=client_plan_nums))

                list_key = "campaign_client:{im_id}:{day_impression_id}".format(im_id=self.im_id,
                                                                                day_impression_id=day.id)
                # 此处会占大量内存
                client_ids = self.redis.lrange(self.wrapper_redis_key(list_key), 0, -1) # 复制全部到 python 中

                nums = int(client_plan_nums) # 这一小时的 client 总量

                while nums > 0:
                    if not client_ids:
                        break

                    client_id = random.choice(client_ids) # 随机从 list 中选一个
                    client_ids.remove(client_id) # 移除

                    key = "campaign_client:{id}:{day_impression_id}".format(id=client_id,
                                                                            day_impression_id=day.id)
                    client = self.redis.hgetall(self.wrapper_redis_key(key))
                    client["actual_plan_impression"] = int(client["actual_plan_impression"])

                    if client["actual_plan_impression"] == 0:
                        self.redis.lrem(self.wrapper_redis_key(list_key), 0, client_id) # 移除 actual_plan_impression 为 0 的
                        key = "campaign_client:{id}:{day_impression_id}".format(id=client_id,
                                                                                day_impression_id=day.id)
                        self.redis.delete(self.wrapper_redis_key(key))
                        continue

                    key = "campaign_client:{id}:{day_impression_id}".format(id=client["id"],
                                                                            day_impression_id=day.id)
                    self.redis.hincrby(self.wrapper_redis_key(key),
                                    "actual_plan_impression",
                                    -1)

                    self.logger.debug("start {im_id}:{day_impression_id}:hour:{hour}:{client_plan_nums}.".\
                                  format(im_id=self.im_id,
                                         day_impression_id=day.id,
                                         hour=hour.targeting_code,
                                         client_plan_nums=nums))

                    CampaignPlanModel.create(impression_master_id=self.im_id,
                                            client_master_id=client["client_id"],
                                            campaign_date="%s %s:%0.2d:%0.2d" % (
                                                day.date, hour.targeting_code,
                                                self.get_minute(),
                                                self.get_seconed()
                                                )
                                            )
                    nums -= 1

                self.logger.debug("end hour:{hour}.".\
                                  format(im_id=self.im_id, day_impression_id=day.id, hour=hour.targeting_code))


        for day in self.di:
            list_key = "campaign_client:{im_id}:{day_impression_id}".format(im_id=self.im_id,
                                                                                day_impression_id=day.id)
            value = self.redis.lpop(self.wrapper_redis_key(list_key))
            while value:
                key = "campaign_client:{id}:{day_impression_id}".format(id=value,
                                                                        day_impression_id=day.id)
                self.redis.delete(self.wrapper_redis_key(key))
                value = self.redis.lpop(self.wrapper_redis_key(list_key))





    def get_minute(self):
        return random.randint(0, 59)

    def get_seconed(self):
        return random.randint(0, 59)

    def get_impression_master_by_id(self, id):
        try:
            im = ImpressionMasterModel.get(ImpressionMasterModel.id == id)
            return im
        except Exception as e:
            self.logger.warning(e)
            return None

    def get_clock_allocation(self):
        try:
            ra = RateAllocationModel.select().where(RateAllocationModel.type == "clock")
            return ra.where(RateAllocationModel.impression_master_id == self.im_id)
        except Exception as e:
            self.logger.warning(e)
            return None

    def get_region_allocation(self):
        try:
            ra = RateAllocationModel.select().where(RateAllocationModel.type == "region")
            return ra.where(RateAllocationModel.impression_master_id == self.im_id)
        except Exception as e:
            self.logger.warning(e)
            return None

    def get_day_impression(self):
        try:
            di = DayImpressionModel.select()
            return di.where(DayImpressionModel.impression_master_id == self.im_id)
        except Exception as e:
            self.logger.warning(e)
            return None
