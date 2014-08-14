#!/usr/bin/env python
# coding: utf-8

# http://flask.pocoo.org/docs/config/#development-production
import os

current_dir = os.path.dirname(__file__)
#cli_file = os.path.join(os.path.dirname(current_dir), "cli.py")
cli_file = os.path.join("/vagrant/supplement", "cli.py")

class Config(object):
    SECRET_KEY = '{SECRET_KEY}'
    SITE_NAME = u'补量'
    CURRENT_DIR = current_dir
    CLI_FILE = cli_file
    SUPERVISOR_LOG_DIR = "/vagrant/supplement/web" #current_dir
    SUPERVISOR_CONFIG_DIR = "/Users/cloverstd/Vagrant/joyplus/php/supplement/web" # current_dir
    SUPERVISOR_RPC_URI = "http://localhost:9001/RPC2"
    PYTHON_PATH = "python"

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestConfig(Config):
    DEBUG = False
    TESTING = True

class DevelopmentConfig(Config):
    '''Use "if app.debug" anywhere in your code, that code will run in development code.'''
    DEBUG = True
    TESTING = True

