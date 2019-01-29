#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import json
import random
import socket
import sqlite3

import requests
import socks

from lib import login_verify, create_role

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 9.0.1; en-us;) AppleWebKit/533.1 (KHTML, like Gecko) Version/5.0 Mobile Safari/533.1"
}

def make_imei():
    return "".join(str(random.randint(0,9)) for x in range(1, len("863272039030961")+1))

def rchr(length):
    d = "0123456789abcdefghijklmnopqrstuvwxyz"
    return "".join(d[random.randint(0, len(d)-1)] for i in range(length))


def create_account(email, imei, proxy):
    # passwd is 123456
    # create and login(2 step)
    # return token, uid
    data = '{"uid":"","token":"","uName":%s,"nickName":"","password":"V0\/wJekk6Kk=","version":"Android1.0.5","imei":"863272039030961","authCode":"","flag":%s,"isfast":"0","thirdType":%s,"thirdToken":"","thirdUid":"","fbBusinessToken":"","language":"En","appKey":"76749c0621384a96b744ccb089567bcf"}'
    url = "http://haiwaitest.3333.cn:8008/sdk/user/user.do"
    # create
    res = requests.post(url, headers=headers, data=data % (email, 0, -1)).json()
    assert res, res["code"] == 100
    # response should be like:
    #{
    #    "code": 100,
    #    "desc": "Success",
    #    "flag": 0,
    #    "isfast": 0,
    #    "token": "",
    #    "token1": "",
    #    "uid": "a68aa880611543a0a7f5a068709d3c84",
    #    "uid1": "",
    #    "uName": "xh4@meirishentie.com",
    #    "thirdType": "0"
    #}
    # login
    res = requests.post(url, headers=headers, data=data % (email, 1, 1)).json()
    assert res, res["code"] == 100
    # response should be like:
    # {
    #     "code": 100,
    #     "desc": "Success",
    #     "flag": 1,
    #     "isfast": 0,
    #     "token": "8522d56093814d68965f9e79894e5064",
    #     "token1": "",
    #     "uid": "a68aa880611543a0a7f5a068709d3c84",
    #     "uid1": "",
    #     "uName": "xh4@meirishentie.com",
    #     "thirdType": "1"
    # }
    return res["token"], res["uid"]


def serverlist(arg1):
    """TODO: Docstring for serverlist.

    :arg1: TODO
    :returns: TODO

    """
    pass

def make_logon_data(version, user_id, imei, session):
    package_data = b'\x09'
    package_data += bytes(version, 'utf8')
    package_data += b'\x14\x00\x04\x00\x07'
    package_data += b'a8_card'
    package_data += b'\x00\x20'
    package_data += bytes(user_id, 'utf8')
    package_data += b'\x0f'
    package_data += bytes(imei+';Android OS 9.0.1 / API-28 (V417IR/eng.root.20190101.162559)', 'utf8')
    package_data += b'\x0c'
    package_data += b'HuaweiMate20@'
    package_data += b'\xac'
    package_data += bytes(session, 'utf8')
    logon_data = len(package_data).to_bytes(4, byteorder='big') + package_data
    # print(logon_data)
    return logon_data

if __name__ == "__main__":
    version = '1.5.60090'
    socket.socket = socks.socksocket
    HOST = '128.14.230.246'
    PORT = 30000
    with open("proxy.txt", "r") as f:
        proxies = f.readlines()
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS guards (email varchar unique, name varchar unique, role_id int)")
    for idx in range(1, 1000):
        try:
            random.shuffle(proxies)
            host, port = proxies[0].strip().split()
            http_proxy = "http://{}:{}".format(host, port)
            email = "{}@gmail.com".format(rchr(random.randint(7,17)))
            device_id = make_imei()
            print("creating account:", email)
            token, user_id = create_account(email, device_id, proxy=http_proxy)
            session = login_verify(user_id, token, version=version, proxy=http_proxy)
            print("creating role")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                s.send(make_logon_data(version, user_id, device_id, session))
                s.settimeout(2)
                while True:
                    try:
                        data = s.recv(2048)
                        # print(data)
                    except socket.timeout:
                        s.settimeout(None)
                        print("all data received!")
                        break
                role_id, name = create_role(s)
                print("role_id:", role_id, "name:", name)
                c.execute("INSERT INTO guards VALUES (?, ?, ?)", (email, name, role_id))
            time.sleep(5)
        except:
            import traceback
            print("ERROR HAPPENS:\n", traceback.format_exc())
