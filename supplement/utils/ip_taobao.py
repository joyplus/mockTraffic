#!/usr/bin/env python
# encoding: utf-8


import json
import urllib2
IP_SOURCE = "http://ip.taobao.com/service/getIpInfo.php?ip={ip}"

def get_ip_info(ip):
    result = urllib2.urlopen(IP_SOURCE.format(ip=ip)).read()
    if result:
        result = json.loads(result)
    return result
