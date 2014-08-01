#!/usr/bin/env python
# encoding: utf-8

import sys
from lib import logger
from script.client_master import ClientMaster

scripts = {
        "client_master": ClientMaster,
        }

def main():
    script = None
    if len(sys.argv) > 1:
        script = sys.argv[1]
        params = sys.argv[2:]
        if scripts.get(script):
            scripts[script]().run(*params)
        else:
            logger.warning("no script " + script)



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
    except Exception as e:
        logger.error(e.message)
        exit(1)
