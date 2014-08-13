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
import pdb


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

        for day in self.di:
            impression = day.impression
            #client_num = day.client

            if impression <= 0:
                continue

            for hour in self.clock_rate:
                client_plan_nums = impression * hour.rate / 100; # 一小时的 client
                try:
                    ExceptionContinueModel.get(day_impression_id=day.id,
                                               type="allot_plan",
                                               targeting_code=hour.targeting_code,
                                               hour=hour.targeting_code,
                                               nums=int(client_plan_nums))
                    self.logger.debug("已经分配过了")
                    continue
                except ExceptionContinueModel.DoesNotExist:
                    pass

                self.logger.debug("开始分配")
                rand_mysql = """
                SELECT * FROM `bl_campaign_client` AS t1\
                JOIN (SELECT ROUND(RAND() * ((SELECT MAX(id) FROM `bl_campaign_client`)-(SELECT MIN(id) FROM `bl_campaign_client`))+(SELECT MIN(id) FROM `bl_campaign_client`)) AS id) AS t2
                WHERE t1.id >= t2.id and t1.plan_impression > 0 and t1.actual_plan_impression > 0 and t1.day_impression_id = {day_im_id}
                ORDER BY t1.id LIMIT 1;
                """

                client_used_list = list() # 用完的 client
                nums = int(client_plan_nums)

                while nums > 0:
                    client = CampaignClientModel.raw(rand_mysql.format(day_im_id=day.id)).execute() # 随机取一条数据
                    try:
                        client = client.next()
                    except StopIteration:
                        continue

                    if client.id in client_used_list:
                        continue

                    client.actual_plan_impression -= 1
                    client.save()
                    client_used_list.append(client.id)

                    CampaignPlanModel.create(impression_master_id=self.im_id,
                                             client_master_id=client.client_id,
                                             campaign_date="%s %s:%0.2d:%0.2d" % (
                                                 day.date, hour.targeting_code,
                                                 self.get_minute(),
                                                 self.get_seconed()
                                                )
                                             )
                    nums -= 1


                ExceptionContinueModel.create(day_impression_id=day.id,
                                                type="allot_plan",
                                                targeting_code=hour.targeting_code,
                                                hour=hour.targeting_code,
                                                nums=int(client_plan_nums))

        sql = """
        delete from bl_exception_continue where day_impression_id = {}
        """
        for day in self.day_im:
            ExceptionContinueModel.raw(sql.format(day.id))


        if impression_master_id: # 从 cli 启动时退出
            self.exit_supervisor()

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
