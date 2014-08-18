#!/usr/bin/env python
# coding: utf-8

# http://www.ipaddresslocation.org/ip_ranges/get_ranges.php
# get CN_ipranges.txt
import json

filename = "../data/CN_ipranges.txt"
ip_data = "../data/ip_range.json"
from ip_taobao import get_ip_info


data = list()
file_bak = open("ip.json", "w+")
with open(filename, "r") as fp:
    for lines in fp.readlines():
        ip_start = lines.split("-")[0].strip()
        ip_end = lines.split("-")[1].strip()
        ip_start_info = get_ip_info(ip_start)
        ip_end_info = get_ip_info(ip_end)
        if ip_start_info["code"] == 0 and ip_end_info["code"]==0:
            ip_start_info = ip_start_info["data"]
            ip_end_info = ip_end_info["data"]
            temp_start = dict(ip=ip_start,
                              country=ip_start_info["country"],
                              area=ip_start_info["area"],
                              region=ip_start_info["region"],
                              city=ip_start_info["city"],
                              isp=ip_start_info["isp"]
                              )
            temp_end = dict(ip=ip_end,
                              country=ip_end_info["country"],
                              area=ip_end_info["area"],
                              region=ip_end_info["region"],
                              city=ip_end_info["city"],
                              isp=ip_end_info["isp"]
                              )
            data.append(dict(start=temp_start, end=temp_end))
            print ip_start, ip_end
            file_bak.writelines(json.dumps(dict(start=temp_start, end=temp_end)))
    fp.close()

if data:
    with open(ip_data, "w") as fp:
        fp.write(json.dumps(data))
        fp.close()
