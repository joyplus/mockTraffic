#!/usr/bin/env python
# encoding: utf-8

from script import BaseScript
from script.allot_day_client import AllotDayClientScript
from script.allot_plan import AllotPlanScript


class CombineTaskScript(BaseScript):
    """
    逐次执行 allot_day_client 和 allot_plan
    """

    def __init__(self, impression_master_id=None):
        super(CombineTaskScript, self).__init__()
        self.im_id = impression_master_id

    def run(self, impression_master_id=None):
        if not impression_master_id and not self.im_id:
            self.logger.error("[CombineTaskScript]: no impression_master_id")
            return

        allot_day_client = AllotDayClientScript(impression_master_id)
        allot_day_client.run()

        allot_plan = AllotPlanScript(impression_master_id)
        allot_plan.run()

        if impression_master_id:
            self.exit_supervisor()
