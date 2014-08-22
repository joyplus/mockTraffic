#!/usr/bin/env python
# encoding: utf-8

from fabric.api import local, settings, env, put, cd, run, hide
from fabric.colors import green, blue, red

env.hosts = ["10.6.2.12"]
env.user = "yangyi"

package_name="supplement.tar.gz"
host_python_path = "/home/yangyi/.virtualenv/supplement"
host_python_env = "/home/yangyi/.virtualenv/supplement/bin/python"
host_python_bin = "/home/yangyi/.virtualenv/supplement/bin"

code_dir = "/home/yangyi/supplement"

def package():
    exclude_file = ["*.log", "supplement.tar.gz", "*.pyc", "*.supplement"]
    exclude_file = ["--exclude={file}".format(file=i) for i in exclude_file]
    exclude_file = " ".join(exclude_file)
    rm_package = "rm -rf {package_name}".format(package_name=package_name)
    with settings(warn_only=True):
        local(rm_package)
    tar = "tar {exclude} -czf {package_name} ./*".format(exclude=exclude_file, package_name=package_name)
    local(tar)


def deliver():
    put(package_name, "/tmp/{package_name}".format(package_name=package_name))
    with settings(warn_only=True):
        run("mkdir /tmp/supplement")
    with cd("/tmp"):
        run("tar zxf /tmp/{package_name} -C /tmp/supplement".format(package_name=package_name))


def deploy():
    with settings(warn_only=True):
        run("mv {code_dir} {code_dir}.backup".format(code_dir=code_dir))

    run("mv /tmp/supplement {code_dir}".format(code_dir=code_dir))
    with settings(hide("stdout")):
        run("{python_bin}/pip install -r {code_dir}/requirements.txt".format(python_bin=host_python_bin,
                                                                             code_dir=code_dir))
    run("cp /home/yangyi/supplement.ini {code_dir}/config.ini".format(code_dir=code_dir))
    run("cp /home/yangyi/config.py {code_dir}/web".format(code_dir=code_dir))

def clear():
    rm_package = "rm -rf {package_name}".format(package_name=package_name)
    with settings(warn_only=True):
        local(rm_package)

def work():
    print green("pack")
    package()
    print green("put package to server")
    deliver()
    print green("deploy code")
    deploy()
    clear()
