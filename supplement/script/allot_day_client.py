#!/usr/bin/env python
# encoding: utf-8

#
# 分配每天的客户端和每个客户端的曝光次数
#

from script import BaseScript
from models.day_impression import DayImpressionModel
from models.campaign_client import CampaignClientModel
from models.client_master import ClientMasterModel
from models.rate_allocation import RateAllocationModel
from models.exception_continue import ExceptionContinueModel
from script.cal_impression import CalculatorScript
import random
from peewee import fn


class AllotDayClientScript(BaseScript):

    client_rate = CalculatorScript.client_rate

    def __init__(self, impression_master_id=None):
        super(AllotDayClientScript, self).__init__()
        self.im_id = self.day_im = None

        if impression_master_id:
            self.im_id = impression_master_id
            self.day_im = self.get_day_impression_by_id(self.im_id)
            self.region_rate = self.get_region_rate_by_id(self.im_id)

        self.total_clients = self.count

    def run(self, impression_master_id=None):
        if impression_master_id:
            self.im_id = impression_master_id
            self.day_im = self.get_day_impression_by_id(self.im_id)
            self.region_rate = self.get_region_rate_by_id(self.im_id)

        if not self.day_im:
            self.logger.error("[AllotDayClientScript]: no day_impression")
            return

        # 第一天
        day_first = self.day_im[0]

        total_client = day_first.client
        clients = self.get_clients(total_client)
        for code, client, nums in clients:  # divide by region
            start = 0
            end = 0
            # 异常处理，continue
            try: # 当异常处理表有记录时，表示已经执行过了
                ExceptionContinueModel.get(ExceptionContinueModel.day_impression_id==day_first.id,
                                                    targeting_code=code,
                                                    type="allot_day_client").nums
                self.logger.debug(u"处理过了 %s %s" % (day_first.date, code))
                continue
            except ExceptionContinueModel.DoesNotExist:
                for i, per in enumerate(self.client_rate):
                    client_rate_num = nums * float(per) / 100
                    #impression = round(client_rate_num * i)
                    end = int(round(client_rate_num)) + start
                    for j in client[start:end]:
                        CampaignClientModel(day_impression_id=day_first.id,
                                            client_id=j.id,
                                            actual_plan_impression=i,
                                            plan_impression=i).\
                            save()
                    start = end

                ExceptionContinueModel.create(day_impression_id=day_first.id,
                                              type="allot_day_client",
                                              targeting_code=code,
                                              nums=nums).save()


        day_left = self.day_im[1:]
        try:
            ExceptionContinueModel.get(ExceptionContinueModel.day_impression_id==day_left[0].id,
                                                type="allot_day_client")
            self.logger.debug("已经分配过了")
        except ExceptionContinueModel.DoesNotExist:
            # 清除已经异常时分配的任务
            self.logger.debug("开始分配")
            # 其他天
            # 复制第一天的 client 的 80% 到其他天
            for day in day_left:
                CampaignClientModel.raw("insert into bl_campaign_client(day_impression_id, client_id, plan_impression) select %d as day_impression_id, client_id, -1 as plan_impression from bl_campaign_client where bl_campaign_client.day_impression_id = %d;" % (day.id, day_first.id)).\
                    execute()

            region_sql = """
            SELECT t2.province_code as region_code, count(t2.province_code) as nums FROM `bl_campaign_client` as t1
            left join `bl_client_master` as t2
            on t2.id = t1.client_id and t1.day_impression_id = {day_impression_id}
            group by t2.province_code order by t2.province_code;
            """
            for day in day_left:
                count = CampaignClientModel.select().\
                    where(CampaignClientModel.day_impression_id == day.id).\
                    count()
                # 去除第一天里 20% 的client
                # TODO: 优化 mysql rand()
                rv = CampaignClientModel.raw("delete from bl_campaign_client where day_impression_id = %d order by rand() limit %d" % (day.id, int(0.2 * count))).\
                    execute()
                # 去除后的 client，如果当日各个地区的大于则去除，小于则补充
                rv = CampaignClientModel.raw(region_sql.format(day_impression_id=day.id)).execute()
                regions = dict()
                for i in rv:
                    regions[i.region_code] = i.nums

                total_client = day.client
                for region in self.region_rate:
                    nums = region.rate * total_client / 100
                    nums = int(round(nums))
                    if regions.get(region.targeting_code):
                        if nums > regions[region.targeting_code]: # 量不足
                            diff = nums - regions[region.targeting_code]

                            addtion_sql = """
                            insert into bl_campaign_client(client_id, day_impression_id)
                            select t1.id, {day_im_id} as day_impression_id from bl_client_master as t1
                            left join bl_campaign_client as t2 on t1.id = t2.client_id
                            where t1.province_code ="{targeting_code}" and t2.id is NULL limit {nums};
                            """
                            # 补充，TODO 未随机
                            addtion_clients = ClientMasterModel.raw(addtion_sql.format(day_im_id=day.id,
                                                                                    targeting_code=region.targeting_code,
                                                                                    nums=diff)).execute()
                        elif nums < regions[region.targeting_code]: # 量过了，不删，plan_impression 为 0 即不使用
                            pass

                    else: # 没有此地区，增加
                        if nums > 0:
                            addtion_sql = """
                            insert into bl_campaign_client(client_id, day_impression_id)
                            select t1.id, {day_im_id} as day_impression_id from bl_client_master as t1
                            left join bl_campaign_client as t2 on t1.id = t2.client_id
                            where t1.province_code ="{targeting_code}" and t2.id is NULL limit {nums};
                            """
                            # 补充，TODO 未随机
                            addtion_clients = ClientMasterModel.raw(addtion_sql.format(day_im_id=day.id,
                                                                                    targeting_code=region.targeting_code,
                                                                                    nums=nums)).execute()
        self.logger.debug("开始设置剩余天数的频次")
        # 设置剩余天数的 actual_plan_impression
        for day in day_left:
            region_client_sql = """
            select t1.* from bl_campaign_client as t1
            left join bl_client_master as t2 on t2.id = t1.client_id
            where t1.day_impression_id = {day_im_id} and t2.province_code = "{targeting_code}"
            """
            region_client_count_sql = """
            select count(*) as nums from bl_campaign_client as t1
            left join bl_client_master as t2 on t2.id = t1.client_id
            where t1.day_impression_id = {day_im_id} and t2.province_code = "{targeting_code}"
            """
            for region in self.region_rate: # 地区的 client
                clients = CampaignClientModel.raw(region_client_sql.format(day_im_id=day.id,
                                                                        targeting_code=region.targeting_code)).\
                    tuples().execute()
                nums = CampaignClientModel.raw(region_client_count_sql.format(day_im_id=day.id,
                                                                        targeting_code=region.targeting_code)).\
                    dicts().execute()
                nums = nums.next()["nums"]
                start = 0
                end = 0
                # 异常处理，continue
                try: # 当异常处理表有记录时，表示已经执行过了
                    ExceptionContinueModel.get(ExceptionContinueModel.day_impression_id==day.id,
                                                    targeting_code=region.targeting_code,
                                                    type="allot_day_client").nums
                    self.logger.debug(u"设置过了, %s, %s" % (day.date, region.targeting_code))
                    continue
                except ExceptionContinueModel.DoesNotExist:
                    self.logger.debug("开始设置")
                    client = clients.cursor.fetchall() # this is a row objects

                    for i, per in enumerate(self.client_rate):
                        self.logger.debug("%s, %s" % (i, per))
                        client_rate_num = nums * float(per) / 100
                        #impression = round(client_rate_num * i)
                        end = int(round(client_rate_num)) + start
                        # TODO: 这里慢
                        for j in client[start:end]:
                                c = CampaignClientModel.get(CampaignClientModel.id == j[0])
                                c.actual_plan_impression = i
                                c.plan_impression = i
                                c.save()
                        start = end
                    self.logger.debug("%s, %s" % (day.date, region.targeting_code))
                    ExceptionContinueModel.create(day_impression_id=day.id,
                                                type="allot_day_client",
                                                targeting_code=region.targeting_code,
                                                nums=nums).save()

        # 更新 day_impression 的 impression
        for day in self.day_im:
            #count = CampaignClientModel.select().\
                #where(CampaignClientModel.day_impression_id == day.id, CampaignClientModel.plan_impression > 0).\
                #count()
            sql = """
            update bl_day_impression\
            set impression =\
            (select sum(plan_impression) from `bl_campaign_client` where day_impression_id = {day_im_id})\
            where id = {day_im_id};
            """
            #day.impression = count
            #day.save()
            CampaignClientModel.raw(sql.format(day_im_id=day.id)).execute()

        sql = """
        delete from bl_exception_continue where day_impression_id = {}
        """
        for day in self.day_im:
            ExceptionContinueModel.raw(sql.format(day.id))

        if impression_master_id: # 从 cli 启动时需要退出
            self.exit_supervisor()


    def get_addition_clients(self, targeting_code, num, day_im_id):
        """
        向 campaign_client 里补充 num 个 client
        """
        #clients = list()
        try_max = 100
        try_temp = 0
        while num > 0:
            client = self.get_client_by_region(targeting_code)
            if not client:
                num -= 1
                continue

            if try_temp > try_max:
                break
            try:
                DayImpressionModel.get().where(DayImpressionModel.day_impression_id == day_im_id,
                                               DayImpressionModel.client_id == client.id)
            except:
                # clients.append(client)
                CampaignClientModel(day_impression_id=day_im_id,
                                    client_id=client.id,
                                    actual_plan_impression=0).\
                    save()
            else:
                try_temp += 1
                continue

            try_temp = 0
            num -= 1

    def get_regions_num_dict(self, total_client):
        regions = dict()
        for region in self.region_rate:
            nums = region.rate / 100 * total_client
            regions[region.targeting_code] = nums

        return regions

    def get_clients_id(self, day_im_id):
        """
        从 campaign_client 里获取已经有的 client
        """
        try:
            clients = CampaignClientModel.select(CampaignClientModel.client_id)
            return clients.where(CampaignClientModel.day_impression_id == day_im_id)
        except Exception as e:
            self.logger.warning(e)
            return None

    def get_clients(self, total_client):
        all_clients = list()
        for region in self.region_rate:
            nums = region.rate / 100 * total_client
            clients = self.get_clients_by_region(
                region.targeting_code, int(round(nums)))
            all_clients.append(clients)

        return all_clients

    def get_clients_by_region(self, targeting_code, nums):
        try:
            clients = ClientMasterModel.select(ClientMasterModel.id)
            return targeting_code, clients.where(ClientMasterModel.province_code == targeting_code).\
                order_by(fn.Rand()).limit(nums), nums
        except Exception as e:
            self.logger.warning(e)
            return None

    def get_region_rate_by_id(self, id):
        try:
            region_rate = RateAllocationModel.select()
            return region_rate.where(RateAllocationModel.impression_master_id == id,
                                     RateAllocationModel.type == "region")
        except Exception as e:
            self.logger.warning(e)
            return None

    def get_day_impression_by_id(self, id):
        try:
            day_im = DayImpressionModel.select()
            return day_im.where(DayImpressionModel.impression_master_id == id)
        except Exception as e:
            self.logger.warning(e)
            return None

    def get_client_by_region(self, targeting_code):
        try:
            client = ClientMasterModel.select().\
                where(ClientMasterModel.province_code == targeting_code).\
                order_by(fn.Rand()).limit(1)
            return client[0]
        except Exception as e:
            self.logger.warning(e)
            return None

    def get_client_by_id(self, id):
        try:
            client = ClientMasterModel.get(ClientMasterModel.id == id)
            return client
        except Exception as e:
            self.logger.warning(e)
            return None

    def get_clients_by_day_im_id(self, id, targeting_code):
        try:
            sql = 'SELECT * FROM `bl_campaign_client` as bcc left join bl_client_master as bcm on bcm.province_code ="%s"  WHERE bcc.`day_impression_id` = %d'
            clients = CampaignClientModel.raw(sql % (targeting_code, id))
            return clients
        except Exception as e:
            self.logger.warning(e)
            return None

    @property
    def count(self):
        clients = ClientMasterModel.select()
        return clients.count()
