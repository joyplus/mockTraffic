#!/usr/bin/env python

import datetime
import math
import ConfigParser
import os
import xmlrpclib


def datetimeformat(value):
    delta = datetime.datetime.now() - value
    if delta.days == 0:
        formatting = 'today'
    elif delta.days < 10:
        formatting = '{0} days ago'.format(delta.days)
    elif delta.days < 28:
        formatting = '{0} weeks ago'.format(int(math.ceil(delta.days / 7.0)))
    elif value.year == datetime.datetime.now().year:
        formatting = 'on %d %b'
    else:
        formatting = 'on %d %b %Y'
    return value.strftime(formatting)


def html5date2py(value):
    return datetime.datetime.strptime(value, "%Y-%m-%d")


def set_supervisor_config(app, name, task, args, numprocs=1):
    """
    name = impression_master_id
    """
    config = ConfigParser.RawConfigParser()
    program = "program:{name}_{task}".format(name=name, task=task)
    config.add_section(program)
    command = "{py_path} {cli} {task} {args}".format(py_path=app.config["PYTHON_PATH"], cli=app.config["CLI_FILE"], task=task, args=args)
    config.set(program, "command", command)
    if int(numprocs) > 1:
        config.set(program, "process_name", "%(program_name)s_%(process_num)02d")
    config.set(program, "numprocs", numprocs)
    config.set(program, "autorestart", "unexpected")
    config.set(program, "autostart", "false")
    config.set(program, "exitcodes", "11")
    config.set(program, "directory", os.path.dirname(app.config["CLI_FILE"]))
    config.set(program, "stderr_logfile", os.path.join(
        app.config["SUPERVISOR_LOG_DIR"], "{name}_{task}_error.log".format(name=name, task=task)))
    config.set(program, "stdout_logfile", os.path.join(
        app.config["SUPERVISOR_LOG_DIR"], "{name}_{task}_info.log".format(name=name, task=task)))

    config_file = os.path.join(app.config["SUPERVISOR_CONFIG_DIR"], "{name}_{task}.supplement".format(name=name, task=task))
    with open(config_file, "wb") as configfile:
            config.write(configfile)
