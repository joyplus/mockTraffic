#!/usr/bin/env python
# encoding: utf-8

from utils.ip_builder import generate as get_ip
from utils.ip_divide import find_city
from utils.mac_builder import generate as get_mac, mac_md5 as get_mac_md5
from utils.ip_taobao import get_ip_info
from script import BaseScript
from models.client_master import ClientMasterModel
import random


class ClientMaster(BaseScript):
    province_code_total = 32

    def __init__(self, province_code=None, init_total=20000, update_percent=20):
        self.total = init_total
        self.province_code = province_code
        self.update_percent = update_percent

        super(ClientMaster, self).__init__()

    def run(self, *args):
        current_task = "init"
        if len(args) > 0:
            current_task = args[0]

        if len(args) == 2:
            self.province_code = args[1]

        if current_task == "init":
            if len(args) == 3:
                self.province_code = args[1]
                self.total = int(args[2])
            self.init()
        else:
            if len(args) == 3:
                self.province_code = args[1]
                self.update_percent = int(args[2])
            self.update()


    @property
    def count(self):
        clients = ClientMasterModel.select()
        return clients.count()


    def update(self, percent=None):
        percent = percent or self.update_percent
        if percent < 0 or percent > 100:
            percent = 20

        self.total_update = self.count * percent / 100

        count = 0
        while count < self.total_update:
            id = random.randint(0, self.count-1)
            client = self.get_client_by_id(id)
            if not client:
                continue
            info = self.get_client_info()
            if not info:
                continue
            if self.exist_ip(info["ip"]):
                continue
            if self.exist_mac_md5(info["mac_md5"]):
                continue

            self.logger.debug(info)
            self.save_client(client, info)

    def exist_mac_md5(self, mac_md5):
        client_sql = ClientMasterModel.select().where(ClientMasterModel.mac_md5==mac_md5)
        return bool(client_sql.exists())

    def exist_ip(self, ip):
        client_sql = ClientMasterModel.select().where(ClientMasterModel.ip==ip)
        return bool(client_sql.exists())

    def init(self):
        count = 0
        while count < self.total:
            info = self.get_client_info()
            if not info:
                continue
            client = self.get_client(info["mac_md5"])

            self.save_client(client, info)
            self.logger.debug(info)
            count += 1

    def get_client_info(self):
        if self.province_code:
            province_code = self.province_code
        else:
            province_code = self.get_province_code()
        ip = get_ip(province_code)
        ip_info = get_ip_info(ip)
        if ip_info["code"] != 0 or not ip_info["data"]["city"]:
            return None
        city = find_city(ip_info["data"]["city"])
        if not city:
            return None
        city_code = city["region_code"]

        mac = get_mac()
        mac_md5 = get_mac_md5(mac)

        return dict(mac=mac, mac_md5=mac_md5, ip=ip,
                    city_code=city_code, province_code=province_code)


    def get_province_code(self):
        p = random.randint(1, self.province_code_total-1)
        return "CN_%02d" % p

    def get_client(self, mac_md5):
        try:
            client = ClientMasterModel.get(ClientMasterModel.mac_md5==mac_md5)
        except Exception as e:
            client = ClientMasterModel()
        return client

    def get_client_by_id(self, id):
        try:
            client = ClientMasterModel.get(ClientMasterModel.id==id)
        except Exception as e:
            client = None
        return client

    def save_client(self, client, info):
        client.mac = client.mac or info["mac"]
        client.mac_md5 = client.mac_md5 or info["mac_md5"]
        client.ip = client.ip or info["ip"]
        client.province_code = client.province_code or info["province_code"]
        client.city_code = client.city_code or info["city_code"]

        client.save()
