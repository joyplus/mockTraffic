#!/usr/bin/env python
# encoding: utf-8


from models.client_master import ClientMasterModel
from models.impression_allocation import ImpressionAllocationModel
from models.day_impression import DayImpressionModel
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

        for day in self.di:
            impression = day.impression
            client_num = day.client
            single_bit_impression = 0
            single_bit_client = 0
            if impression <= 0:
                continue

            for hour in self.clock_rate: # 每一小时的投放量
                for region in self.region_rate: # 每一地区的这一小时的投放量
                    sql = """
                    SELECT t1.* FROM `bl_campaign_client` as t1
                    left join `bl_client_master` as t2 on t2.id = t1.client_id
                    where t1.day_impression_id = {day_im_id} and t2.province_code = "{targeting_code}"
                    """
                    clients = CampaignClientModel.raw(sql.format(day_im_id=day.id,
                                                                 targeting_code=region.targeting_code)).execute()
                    clients = clients.cursor.fetchall()
                    clients_count = len(clients)
                    use_index = list()

                    single_bit_impression = impression * hour.rate / 100
                    single_bit_impression = round(single_bit_impression) * region.rate / 100
                    single_bit_impression = int(round(single_bit_impression))

                    single_bit_client = client_num * hour.rate / 100
                    single_bit_client = round(single_bit_client) * region.rate / 100
                    single_bit_client = int(round(single_bit_client))
                    #print "region: %r" % region.targeting_code,
                    #print single_bit_impression, single_bit_client
                    #print "campaign time", day.date, hour.targeting_code, len(clients)
                    while single_bit_impression > 0:
                        client_index = random.randint(0, clients_count-1)

                        if client_index in use_index:
                            continue
                        if not clients[client_index]:
                            continue

                        campaign_client_id = clients[client_index][0]
                        use_index.append(client_index)

                        client = CampaignClientModel.get(CampaignClientModel.id == campaign_client_id)
                        if client.plan_impression <= 0:
                            continue
                        if client.actual_plan_impression <= 0:
                            continue

                        client.actual_plan_impression -= 1
                        client.save()
                        plan = CampaignPlanModel(impression_master_id=self.im_id,
                                                 client_master_id=client.client_id,
                                                 campaign_date="%s %s:%0.2d:%0.2d" % (day.date, hour.targeting_code, self.get_minute(), self.get_seconed())
                                                 )
                        plan.save()


                        single_bit_impression -= 1



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
