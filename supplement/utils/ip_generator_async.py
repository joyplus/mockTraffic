#!/usr/bin/env python
# coding: utf-8

# http://www.ipaddresslocation.org/ip_ranges/get_ranges.php
# get CN_ipranges.txt
import urllib2
import json
import gevent
import gevent.monkey
from ip_taobao import get_ip_info
gevent.monkey.patch_socket()

filename = "../data/CN_ipranges.txt"
ip_data = "../data/ip_range2.json"

NUMS = 10


data = list()
ip_lists = list()
with open(filename, "r") as fp:
    for lines in fp.readlines():
        ip_start = lines.split("-")[0].strip()
        ip_end = lines.split("-")[1].strip()
        #ip_start_info = get_ip_info(ip_start)
        #ip_end_info = get_ip_info(ip_end)
        ip_lists.append((ip_start, ip_end))
    fp.close()

def save_ip(ip_start_info, ip_end_info):
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
        print json.dumps(temp_start, ensure_ascii=False)
        print json.dumps(temp_end, ensure_ascii=False)
        data.append(dict(start=temp_start, end=temp_end))

def fetch(ip):
    ip1, ip2 = ip
    print "start",
    print ip1, ip2
    ip_start_info = get_ip_info(ip1)
    ip_end_info = get_ip_info(ip2)
    save_ip(ip_start_info, ip_end_info)

def fetch_bunch(bunch):
    for i in bunch:
        fetch(i)

jobs = list()
step = len(ip_lists)/NUMS
for i in xrange(0, len(ip_lists), step):
    jobs.append(gevent.spawn(fetch_bunch, ip_lists[i:i+step]))

#jobs = [gevent.spawn(fetch_bunch, ip) for ip in ip_lists]
gevent.joinall(jobs)

if data:
    with open(ip_data, "w") as fp:
        fp.write(json.dumps(data))
        fp.close()
