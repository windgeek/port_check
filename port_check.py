#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   port_check_reslove.py
@Time    :   2021/12/15 15:05:24
@Author  :   wind 
'''



import requests
import time
import socket
import logging
import json
import datetime
import subprocess


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
fileHandler = logging.FileHandler('port.log', mode='w', encoding='UTF-8')
fileHandler.setLevel(logging.NOTSET)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)



def cmdout(cmd):
    try:
        out_text = subprocess.check_output(cmd, shell=True).decode('utf-8')
    except subprocess.CalledProcessError as e:
        out_text = e.output.decode('utf-8')
    return out_text



def del_file(filename, delname):
    with open(filename,'r') as r:
        lines=r.readlines()
    with open(filename,'w') as w:
        for l in lines:
            if delname not in l:
                w.write(l)


def check_file(filename, checkname):
    with open(filename,'r') as r:
        all = r.read()
        if checkname in all:
            return True
        elif checkname not in all:
            return False





def put_feishu(message, ptime):
    url = "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxx"
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    botmessage = "------------------------------" + '\n' \
              + "           ops_port_alert"  + '\n' \
              + "------------------------------" + '\n' \
              + "报警: " + message + '\n' \
              + "时间: " + ptime + '\n' \
              + "------------------------------"
    try:
        body = {
            "msg_type": "text",
            "content": {
                "text": botmessage
            }
        }
        # print(body)
        requests.post(url, json.dumps(body), headers=headers)
    except Exception as e:
        print(e)


def put_alert(service, ip, port):
    FMT = '%Y-%m-%d_%H:%M:%S'
    ptime = time.strftime(FMT)
    message = '{} {}:{} 检测不到，请检查服务状态'.format(service, ip, port)
    wmessage = '{} {} {} {}\n'.format(ptime, service, ip, port)
    mmessage = '{} {}'.format(ip, port)
    r_com = []
    if not check_file('alert.db', mmessage):
        with open('alert.db', 'a') as a:
            a.write(wmessage)
        put_feishu(message, ptime)
    elif check_file('alert.db', mmessage):
        with open('alert.db', 'r') as r:
            for l in r.readlines():
                if mmessage in l:
                    r_com.append(l)
            del_file('alert.db', wmessage)
        oldtime = r_com[0].strip().split(' ')[0]
        newtime = wmessage.strip().split(' ')[0]
        tdelta = int((datetime.datetime.strptime(newtime, FMT) - datetime.datetime.strptime(oldtime, FMT)).seconds/60)
        logger.debug(tdelta)
        if tdelta >= 60 and tdelta % 60 == 0:
            ptime = r_com[0].strip().split(' ')[0]
            put_feishu(message, ptime)



def check(service, ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        result = s.connect_ex((ip, port))
        if result == 0:
            message = "The Server IP: {} , Port {} has been used".format(ip, port)
            print(message)
            logger.debug(message)
        else:
            message = "The Server IP: {} , Port {} no response".format(ip, port)
            print(result, message)
            put_alert(service, ip, port)
            logger.debug(message)
        s.close()
    except Exception as e:
        logger.debug(e)
    return result


def check_resolved(service, ip, port):
    FMT = '%Y-%m-%d_%H:%M:%S'
    ptime = time.strftime(FMT)
    check_re = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        result = s.connect_ex((ip, port))
        if result == 0:
            check_re = True
            message = '{} {}:{} 已恢复'.format(service, ip, port)
            put_feishu(message, ptime)
        s.close()
    except Exception as e:
        logger.debug(e)
    return check_re



if __name__ == '__main__':
    cmdout("echo > alert.db")
    while True:
        with open("./port.conf") as f:
            for line in f:
                service = line.strip().split(" ")[0]
                ip = line.strip().split(" ")[1].split(":")[0]
                port = int(line.strip().split(" ")[1].split(":")[1])
                check(service, ip, port)
        cmdout("sed -i '/^$/d' alert.db")
        with open("alert.db") as a:
            for line in a:
                if not line.startswith('#'):
                    service1 = line.strip().split(" ")[1]
                    ip1 = line.strip().split(" ")[2]
                    port1 = int(line.strip().split(" ")[3])
                    # wmessage = '{} {} {} {}\n'.format(ptime, service, ip, port)
                    rmessgae = '{} {} {}'.format(service1, ip1, port1)
                    if check_resolved(service1, ip1, port1):
                        del_file('alert.db', rmessgae)
        time.sleep(600)
