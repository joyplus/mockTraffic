#!/usr/bin/env python
# encoding: utf-8

import xmlrpclib

class Supervisor(object):

    def __init__(self, app):
        self.app = app

        self.server = xmlrpclib.Server(app.config["SUPERVISOR_RPC_URI"])
