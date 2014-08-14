#!/usr/bin/env python

import datetime

from flask import Blueprint, render_template, abort, request, redirect, url_for
from web import app, supervisor
from models.impression_master import ImpressionMasterModel as IMM
from models.day_impression import DayImpressionModel as DIM
from models.rate_allocation import RateAllocationModel as RAM
from models.rate_targeting import RateTargetingModel as RTM
from web.helpers import html5date2py, set_supervisor_config
from flask import jsonify
import httplib
import xmlrpclib

frontend = Blueprint('simple_page', __name__,
                        template_folder='templates')

@frontend.route('/')
def show():
    if app.debug:
        app.logger.debug('rendering index')
    return render_template(
                'index.html',
                config=app.config,
                now=datetime.datetime.now,
            )

@frontend.route("/instance/add", methods=["GET", "POST"])
def instance_add():
    if request.method == "GET":
        return render_template("add_instance.html",
                            config=app.config,
                            )

    tracking_url_1 = request.form["tracking_url_1"]
    tracking_url_2 = request.form["tracking_url_2"]
    tracking_url_3 = request.form["tracking_url_3"]
    campaign_name = request.form["campaign_name"]
    start_date = request.form["start_date"]
    end_date = request.form["end_date"]

    imm = IMM.create(tracking_url_1=tracking_url_1,
                    tracking_url_2=tracking_url_2,
                    tracking_url_3=tracking_url_3,
                    campaign_name=campaign_name,
                    start_date=html5date2py(start_date),
                    end_date=html5date2py(end_date),
                    )
    return redirect("/instance")

@frontend.route("/ajax/instance/<int:id>")
def ajax_instance_status(id):
    day_impression_status = True
    rate_allocation_status = True
    if DIM.select().where(DIM.impression_master_id==id).count() == 0:
        day_impression_status = False

    if RAM.select().where(RAM.impression_master_id==id).count() != 58:
        rate_allocation_status = False

    return jsonify(day_impression_status=day_impression_status,
                   rate_allocation_status=rate_allocation_status)


@frontend.route("/instance", defaults={"page": 1})
@frontend.route("/instance/page/<int:page>")
def instance_list(page):
    per_page = 10
    ims = IMM.select().order_by(IMM.id.desc()).paginate(page, per_page)
    return render_template("instance_list.html",
                           config=app.config,
                           ims=ims,
                           page=page)


@frontend.route("/ajax/instance/d/mod", methods=["POST"])
def day_impression_instance_mod():
    day_id = request.form["id"]
    client = request.form["client"]

    day = DIM.get(DIM.id==day_id)
    day.client = client
    day.save()
    return jsonify(status=True)



@frontend.route("/instance/d/<int:id>")
def day_impression_instance(id):
    dims = DIM.select().where(DIM.impression_master_id==id)
    im = IMM.get(IMM.id==id)
    return render_template("day_impression_instance.html",
                           config=app.config,
                           dims=dims,
                           im=im,
                           )

@frontend.route("/instance/d/<int:id>/add", methods=["GET", "POST"])
def day_impression_instance_add(id):
    im = IMM.get(IMM.id==id)
    if DIM.select().where(DIM.impression_master_id==id).count() > 0:
        return redirect("/instance/d/%s" % id)

    if request.method == "GET":
        day = (im.end_date - im.start_date).days
        days = [im.start_date + datetime.timedelta(i) for i in xrange(day+1)]

        return render_template("day_impression_instance_add.html",
                            config=app.config,
                            im=im,
                            days=days
                            )

    for key, value in request.form.items():
        DIM.create(impression_master_id=id,
                   date=html5date2py(key),
                   client=int(value))
    return redirect("/instance/d/%s" % id)


@frontend.route("/ajax/instance/rate/region/<int:id>")
def rate_region(id):
    rams = RAM.select().where(RAM.impression_master_id==id,
                              RAM.type=="region").order_by(RAM.targeting_code);
    result = dict()
    for i in rams:
        result[str(i.id)] = [i.targeting_code, i.rate]

    return jsonify(**result)

@frontend.route("/ajax/instance/rate/clock/<int:id>")
def rate_clock(id):
    rams = RAM.select().where(RAM.impression_master_id==id,
                              RAM.type=="clock").order_by(RAM.targeting_code);
    result = dict()
    for i in rams:
        result[str(i.id)] = [i.targeting_code, i.rate]

    return jsonify(**result)

@frontend.route("/ajax/instance/rate/mod", methods=["GET", "POST"])
def rate_mod():
    if request.method == "GET":
        return "hi"

    id = request.form["id"]
    rate = request.form["rate"]
    ram = RAM.get(RAM.id==id)
    ram.rate = float(rate)
    ram.save()
    return jsonify(status=True)


@frontend.route("/instance/rate/region/<int:id>/add", methods=["GET", "POST"])
def rate_region_add(id):
    rtm = RTM.select().where(RTM.targeting_type=="region")
    if RAM.select().where(RAM.impression_master_id==id,
                          RAM.type=="region").count() > 0:
        return redirect("/instance/d/%s" % id)

    if request.method == "GET":
        return render_template("rate_region_add.html",
                               config=app.config,
                               rtm=rtm)

    for key, value in request.form.items():
        RAM.create(impression_master_id=id,
                   type="region",
                   rate=float(value),
                   targeting_code=key)

    return redirect("/instance/d/%s" % id)


@frontend.route("/instance/rate/clock/<int:id>/add", methods=["GET", "POST"])
def rate_clock_add(id):
    rtm = RTM.select().where(RTM.targeting_type=="clock")
    if RAM.select().where(RAM.impression_master_id==id,
                          RAM.type=="clock").count() > 0:
        return redirect("/instance/d/%s" % id)

    if request.method == "GET":
        return render_template("rate_region_add.html",
                               config=app.config,
                               rtm=rtm)

    for key, value in request.form.items():
        RAM.create(impression_master_id=id,
                   type="clock",
                   rate=float(value),
                   targeting_code=key)

    return redirect("/instance/d/%s" % id)

@frontend.route("/ajax/supervisor/set_config", methods=["POST"])
def supervisor_set():
    name = request.form["name"]
    task = request.form["task"]
    numprocs = request.form.get("numprocs", 1)
    if not numprocs:
        numprocs = 1
    args = request.form["args"]

    set_supervisor_config(app, name, task, args, numprocs)

    return jsonify(status=True)


@frontend.route("/ajax/supervisor/get_state", methods=["POST"])
def supervisor_get_state():
    try:
        state = supervisor.server.supervisor.getState()
    except httplib.BadStatusLine:
        state = dict(state=111111,
                     statename="DOWNTIME")
    return jsonify(state)


@frontend.route("/ajax/supervisor/restart", methods=["POST"])
def supervisor_restart():
    state = supervisor.server.supervisor.restart()
    return jsonify(status=state)

@frontend.route("/ajax/supervisor/start", methods=["POST"])
def supervisor_start():
    name = request.form["name"]
    task = request.form["task"]
    program = "{name}_{task}".format(name=name, task=task)
    rv = supervisor.server.supervisor.startProcess(program)
    return jsonify(status=rv)

@frontend.route("/ajax/supervisor/start", methods=["POST"])
def supervisor_stop():
    name = request.form["name"]
    task = request.form["task"]
    program = "{name}_{task}".format(name=name, task=task)
    rv = supervisor.server.supervisor.stopProcess(program)
    return jsonify(status=rv)

@frontend.route("/ajax/supervisor/task/state", methods=["POST"])
def supervisor_task_state():
    name = request.form["name"]
    task = request.form["task"]
    program = "{name}_{task}".format(name=name, task=task)
    try:
        rv = supervisor.server.supervisor.getProcessInfo(program)
    except xmlrpclib.Fault:
        rv = dict(state=111111,
                  statename="NONEXISTENCE")
    return jsonify(rv)


@frontend.route("/ajax/supervisor/add_config", methods=["POST"])
def supervisor_add_config():
    name = request.form["name"]
    task = request.form["task"]
    program = "{name}_{task}".format(name=name, task=task)
    rv = supervisor.server.supervisor.addProcessGroup(program)
    return jsonify(status=rv)
