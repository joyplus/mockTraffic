#!/usr/bin/env python
# encoding: utf-8


from script import BaseScript
from models.impression_master import ImpressionMasterModel
from models.day_impression import DayImpressionModel


class CalculatorScript(BaseScript):

    client_rate = [0, 23, 24, 28, 6, 5, 4, 4, 3, 2, 1]  # 开机 0 到 10 次伪正太分布

    def __init__(self):
        super(CalculatorScript, self).__init__()

    def run(self, impression_master_id, name="impression"):
        if impression_master_id:
            self.im_id = impression_master_id
            #self.im = self.get_impression_master_by_id(self.im_id)
            self.day_im = self.get_day_impression_by_id(self.im_id)

        if not self.im_id:
            self.logger.warning("[CalulatorScript]: no day_impression")
            return None

        if name == "impression":
            #self.im.total_impression = CalulatorScript.get_impression(self.im.total_client)
            for im in self.day_im:
                im.impression = CalculatorScript.get_impression(im.client)
                im.save()
                self.logger.debug(
                    "[CalulatorScript]: calculate impression %s" % im.date)
            # self.im.save()
            self.logger.debug("[CalulatorScript]: calculate impression")
        elif name == "client":
            #self.im.total_client = CalulatorScript.get_client(self.im.total_impression)
            # self.im.save()
            for im in self.day_im:
                im.client = CalculatorScript.get_client(im.impression)
                im.save()
                self.logger.debug(
                    "[CalulatorScript]: calculate client %s" % im.date)
            self.logger.debug("[CalulatorScript]: calculate client")

    @classmethod
    def get_impression(self, clients):
        impression = 0

        for i, per in enumerate(self.client_rate):
            #impression += round(clients / float(i) * 100)
            impression += round(clients * float(per)/100 * i) # 客户端 x 百分比 x 曝光次数

        return int(impression)

    @classmethod
    def get_client(self, impression):
        client = 0

        for i in self.client_rate:
            client += round(impression * float(i) / 100)

        return int(client)

    def get_impression_master_by_id(self, id):
        try:
            im = ImpressionMasterModel.get(ImpressionMasterModel.id == id)
            return im
        except Exception as e:
            self.logger.warning(e)
            return None

    def get_day_impression_by_id(self, id):
        try:
            im = DayImpressionModel.select()
            return im.where(DayImpressionModel.impression_master_id == id)
        except Exception as e:
            self.logger.warning(e)
            return None
