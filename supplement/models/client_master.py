#!/usr/bin/env python
# encoding: utf-8

from peewee import CharField, IntegerField
from models.base import BaseModel


class ClientMasterModel(BaseModel):

    id = IntegerField(primary_key=True)
    mac = CharField()
    mac_md5 = CharField()
    ip = CharField()
    province_code = CharField()
    city_code = CharField()
    device_id = IntegerField()

    def __repr__(self):
        return "<ClientMasterModel: %r>" % self.id

    class Meta:
        db_table = "bl_client_master"
