#!/usr/bin/env python
# encoding: utf-8

from models.base import BaseModel
from peewee import CharField, IntegerField


class IpRegionMasterModel(BaseModel):
    id = IntegerField(primary_key=True)
    province_code = CharField()
    ip_address = CharField()

    def __repr__(self):
        return "<IpRegionMasterModel: %r>" % self.id

    class Meta:
        db_table = "bl_ip_region_master"
