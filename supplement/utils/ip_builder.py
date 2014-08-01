#!/usr/bin/env python
# encoding: utf-8

from ip_divide import get_regions
import random
import string

regions = get_regions()

def ip2string(ip):
    a = (ip & 0xff000000) >> 24
    b = (ip & 0x00ff0000) >> 16
    c = (ip & 0x0000ff00) >> 8
    d = ip & 0x000000ff
    return "%d.%d.%d.%d" % (a,b,c,d)

def string2ip(str):
    ss = string.split(str, '.');
    ip = 0L
    for s in ss: ip = (ip << 8) + string.atoi(s)
    return ip;

def generate(province_code):
    province_code = province_code.upper()

    ip_ranges = regions[province_code]
    ip = generate_single(ip_ranges)
    return ip2string(ip)


def generate_single(ip_ranges):
    ranges = random.randint(0, len(ip_ranges)-1)
    ip_range = ip_ranges[ranges]
    ip_range = ip_ranges[0]
    ip_start = string2ip(ip_range[0])
    ip_end = string2ip(ip_range[1])
    return random.randint(ip_start, ip_end)



if __name__ == '__main__':
    print generate("CN_01")
    print generate("CN_29")
    print generate("CN_30")
