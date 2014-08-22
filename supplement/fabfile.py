#!/usr/bin/env python
# encoding: utf-8

from fabric.api import local, settings, env, put, cd, run, hide
from fabric.colors import green, blue, red
import os.path

env.hosts = ["10.6.2.12"]
env.user = "yangyi"
package_name="supplement.tar.gz" # 打包的文件名
code_dir = "/home/yangyi/supplement" # 服务器代码目录
config_file_path = "/home/yangyi" # 服务器代码配置文件的目录
host_python_path = "/home/yangyi/.virtualenv/supplement" # 服务器 python 环境


# supplement cli 配置文件
supplement_config_file = os.path.join(config_file_path, "supplement.ini")
# supplement web 配置文件
web_config_file = os.path.join(config_file_path, "config.py")

host_python_env = os.path.join(host_python_path, "bin/python")
host_python_bin = os.path.join(host_python_path, "bin")


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
    run("cp {supplement_config_file} {code_dir}/config.ini".format(supplement_config_file=supplement_config_file,
                                                                   code_dir=code_dir))
    run("cp {web_config_file} {code_dir}/web".format(web_config_file=web_config_file,
                                                     code_dir=code_dir))

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
