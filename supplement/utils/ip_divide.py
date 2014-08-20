#!/usr/bin/env python
# encoding: utf-8

import json
import re

file_src = "data/ip_range.json"
file_dest = "data/ip_source.json"
regional_targeting = "data/regional_targeting.json"

data = ""
regional = ""
with open(file_src, "r") as fp:
    content = fp.read()
    data = json.loads(content)
    fp.close()

def repl(matchobj):
    return ' "' + matchobj.group(1) + '",'

content = ""
with open(regional_targeting, "r") as fp:
    content = fp.read()
    pattern = ur" (\d+),"
    content = re.sub(re.compile(pattern), repl, content)

    regional = json.loads(content)
    fp.close()

regions = list() # 省
citys = list() # 城市
for i in regional:
    if i["targeting_type"] == "REGION":
        regions.append(i)
    elif i["targeting_type"] == "CITY":
        citys.append(i)

def find_province(province):
    for i in regions:
        if i["region_name"] in province:
            return i["targeting_code"]
    return None

result = dict()

for i in data:
    targeting_code = find_province(i["start"]["region"])
    if targeting_code:
        if not targeting_code in result:
            result[targeting_code] = list()

        result[targeting_code].append((i["start"]["ip"], i["end"]["ip"]))


def find_city(city):
    for i in citys:
        if i["region_name"] == city:
            return i
    return None

def get_regions():
    return result


if __name__ == '__main__':
    print get_regions()["CN_30"]
