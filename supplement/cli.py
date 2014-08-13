#!/usr/bin/env python
# encoding: utf-8

import sys
from lib import logger, config
from script.client_master import ClientMaster
from script.allot_plan import AllotPlanScript
from script.allot_client import AllotClientScript
from script.cal_impression import CalculatorScript
from script.allot_day_client import AllotDayClientScript
from script.put2queue import PutToQueue
from script.send_request import SendRequestScript
from script.get_result import GetResultScript
from script.combine_task import CombineTaskScript
from time import time
from logbook import NullHandler, StreamHandler

scripts = {
        "client_master": ClientMaster,
        "allot_plan": AllotPlanScript,
        "allot_client": AllotClientScript,
        "calculate": CalculatorScript,
        "allot_day_client": AllotDayClientScript,
        "put2queue": PutToQueue,
        "send_request": SendRequestScript,
        "get_result": GetResultScript,
        "combine_task": CombineTaskScript,
        }


script = ""
if len(sys.argv) > 1:
    script = sys.argv[1]

def main():
    if len(sys.argv) > 1:
        script = sys.argv[1]
        params = sys.argv[2:]
        if scripts.get(script):
            scripts[script]().run(*params)
            exit(11)
        else:
            logger.warning("no script " + script)



null_handler = NullHandler()
debug_handler = NullHandler()
info_handler = StreamHandler(sys.stdout, level="INFO")
error_handler = StreamHandler(sys.stderr, level="ERROR")

if config.getboolean("log", "debug"):
    debug_handler = StreamHandler(sys.stdout, level="DEBUG")
    #info_handler = RotatingFileHandler(config.get("log", "info_log_path"), level="INFO", )
    #error_handler = RotatingFileHandler(config.get("log", "error_log_path"), level="ERROR")

formatter_str = "[{record.level_name} {record.time} {record.module}:{record.lineno}]: {record.message}"
info_handler.format_string = formatter_str
error_handler.format_string = formatter_str
debug_handler.format_string = formatter_str


if __name__ == '__main__':
    with null_handler.applicationbound():
        with debug_handler.applicationbound():
            with info_handler.applicationbound():
                with error_handler.applicationbound():
                    start = time()
                    logger.info("start %s: %s" % (script, start))

                    if not config.getboolean("log", "debug"):
                        try:
                            main()
                        except KeyboardInterrupt:
                            exit(0)
                        except Exception as e:
                            logger.error(e)
                            exit(1)
                    else:
                        main()

                    end = time()
                    logger.info("stop: %s" % end)
