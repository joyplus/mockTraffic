#!/usr/bin/env python

import os

# Logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y%m%d-%H:%M%p',
)

# Flask
from flask import Flask
app = Flask(__name__)

# Config
if os.getenv('DEV') == 'yes':
    app.config.from_object('web.config.DevelopmentConfig')
    app.logger.info("Config: Development")
elif os.getenv('TEST') == 'yes':
    app.config.from_object('web.config.TestConfig')
    app.logger.info("Config: Test")
else:
    app.config.from_object('web.config.ProductionConfig')
    app.logger.info("Config: Production")

# Helpers
from web.helpers import datetimeformat
from web.supervisor import Supervisor
app.jinja_env.filters['datetimeformat'] = datetimeformat

supervisor = Supervisor(app)

# http://flask.pocoo.org/docs/patterns/packages/
from web.controllers.frontend import frontend
app.register_blueprint(frontend)
