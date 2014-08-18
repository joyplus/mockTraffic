#!/usr/bin/env python
# encoding: utf-8

#
# @Author: cloverstd
# @Email: cloverstd@gmail.com
# @Date: 2014-07-31 16:54:12
# @Desc: generate mac address
#

import random
import re
import hashlib

BIT_PATTERN = ur"^[a-zA-Z0-9]{2}$"
PREFIX_PATTERN = BIT_PATTERN[1:-1] + "-" + BIT_PATTERN[1:-1] + "-" + BIT_PATTERN[1:-1]
PREFIX_PATTERN = "^" + PREFIX_PATTERN + "$"

def generate(prefix=None, divide=":", upper=False):
    """
    generate mac address
    """

    front = ""
    back = ""
    if prefix and re.match(PREFIX_PATTERN, prefix):
        front = prefix
    else:
        front = divide.join([generate_bit() for i in xrange(3)])
    back = divide.join([generate_bit() for i in xrange(3)])
    if upper:
        front = front.upper()
        back = back.upper()
    return front + divide + back


def generate_bit(exclude=None):
    """
    generate a bit of mac
    """
    bit = random.randint(0x00, 0xff)
    if exclude:
        if re.match(BIT_PATTERN, exclude):
            while exclude == bit:
                bit = random.randint(0x00, 0xff)

    return "%02X" % bit

def mac_md5(mac):
    return hashlib.md5(mac).hexdigest()


if __name__ == '__main__':
    print generate("11-12-1a", "-", True)
    print generate()
    print mac_md5(generate())
