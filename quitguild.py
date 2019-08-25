#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import socket
import time
import json
import datetime
import argparse
import sqlite3
from functools import reduce

import requests

from lib import login_verify, create_role, make_data, get_formation, body_test, make_battle_data, init_data, gen_name, make_login_server_data, make_quick_battle_data
from const import EPISODES, SERVER_LIST, STACK_ABLES, GUILD_ID, version

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 9.0.1; en-us;) AppleWebKit/533.1 (KHTML, like Gecko) Version/5.0 Mobile Safari/533.1"
}

CARDS = set()
GOLD_WINE = 0

def make_imei():
    return "".join(str(random.randint(0,9)) for x in range(1, len("863272039030961")+1))

def rchr(length):
    d = "0123456789abcdefghijklmnopqrstuvwxyz"
    return "".join(d[random.randint(0, len(d)-1)] for i in range(length))


def create_account(email, imei):
    # passwd is 123456
    # create and login(2 step)
    # return token, uid
    data = '{"uid":"","token":"","uName":%s,"nickName":"","password":"V0\/wJekk6Kk=","version":"Android1.0.5","imei":"863272039030961","authCode":"","flag":%s,"isfast":"0","thirdType":%s,"thirdToken":"","thirdUid":"","fbBusinessToken":"","language":"En","appKey":"76749c0621384a96b744ccb089567bcf"}'
    url = "http://haiwaitest.3333.cn:8008/sdk/user/user.do"
    # create
    res = requests.post(url, headers=headers, data=data % (email, 0, -1)).json()
    assert res, res["code"] == 100
    return login_account(email, imei)

def login_account(email, imei):
    # login
    data = '{"uid":"","token":"","uName":%s,"nickName":"","password":"V0\/wJekk6Kk=","version":"Android1.0.5","imei":"863272039030961","authCode":"","flag":%s,"isfast":"0","thirdType":%s,"thirdToken":"","thirdUid":"","fbBusinessToken":"","language":"En","appKey":"76749c0621384a96b744ccb089567bcf"}'
    url = "http://haiwaitest.3333.cn:8008/sdk/user/user.do"
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
    return logon_data

def read_bytes(s, length):
    buf = b""
    while len(buf) < length:
        s.settimeout(2)
        try:
            d = s.recv(length - len(buf))
        except:
            s.settimeout(None)
            break
        if not d:
            break
        buf += d
    return buf


def read_all(s):
    while True:
        try:
            pack = read_one(s)
            if not pack:
                return True
            head, body = pack
        except socket.timeout:
            s.settimeout(None)
            return True

def read_one(s):
    head = read_bytes(s, 4)
    if not head:
        return None
    body = read_bytes(s, int.from_bytes(head, byteorder="big"))
    if head == b"\x00\x00\x00\x09" and body.startswith(b"\x01\x00\x5c\x01\x12"):  # gold wine
        global GOLD_WINE
        GOLD_WINE = int.from_bytes(body[-4:], byteorder="little")
    return head, body

def battle_episode(s, episode):
    s.sendall(make_battle_data(CARDS, episode))
    read_all(s)
    s.sendall(make_data("first_battle_end"))
    read_all(s)

def do_story(s, story):
    sp = story.split()
    if len(sp) == 1:
        # no battle, but card is possible
        s.sendall(b'\x00\x00\x00\x07\x00\x04\x00\x00\x00\x00\x03')
        # try not find any card
        return 0
    else:
        s.sendall(b'\x00\x00\x00\x07\x00\x04\x00\x00\x00\x00\x06')
        times = 0
        for episode in sp[1:]:
            battle_episode(s, episode)
            times += 1
        return times


def do_attend(s, extra=dict()):
    # return value: True need update db, False no need
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    last_attend_day = extra.get("attend")
    if now != last_attend_day:
        s.sendall(b'\x00\x00\x00\x07\x00\x02\x00\x00\x00\x00\xc7')
        extra["attend"] = now
        return True
    return False


def eat_food(s, extra):
    now = datetime.datetime.now()
    if now.hour in range(12, 14):
        key = "food_1"
        data = b"\x00\x00\x00\x08\x00\x03\x00\x00\x00\x00\xc6\x01"
    elif now.hour in range(18, 20):
        key = "food_2"
        data = b"\x00\x00\x00\x08\x00\x03\x00\x00\x00\x00\xc6\x02"
    elif now.hour in range(21, 23):
        key = "food_3"
        data = b"\x00\x00\x00\x08\x00\x03\x00\x00\x00\x00\xc6\x03"
    else:
        return False
    day = now.strftime("%Y-%m-%d")
    if extra.get(key) != day:
        s.sendall(data)
        extra[key] = day
        return True
    return False

def do_daily(s, extra):
    now = datetime.datetime.now()
    if now.hour in (0, 23) and extra.get("daily") != now.strftime("%Y-%m-%d"):  # for testing
        extra["daily"] = now.strftime("%Y-%m-%d")
        # 10 times battle
        s.sendall(b"\x00\x00\x00\x08\x00\x02\x00\x00\x00\x00\xd6\x03")
        # explore card(2 times, 1 free)
        s.sendall(b"\x00\x00\x00\x09\x00\x03\x00\x00\x00\x00\xa3\x01\x00")
        s.sendall(b"\x00\x00\x00\x09\x00\x04\x00\x00\x00\x00\xa3\x01\x00")
        # explore reward
        s.sendall(b"\x00\x00\x00\x08\x00\x05\x00\x00\x00\x00\xd6\x02")
        # guild reward
        s.sendall(b"\x00\x00\x00\x08\x00\x06\x00\x00\x00\x00\xd6\x0e")
        # get mail rewrd when monday
        if now.weekday() == 0:
            s.sendall(b"\x00\x00\x00\x07\x00\x01\x00\x00\x00\x00\x69")
        return True
    return False

def heart_beat(s):
    s.sendall(b"\x00\x00\x00\x02\x01\x00")

def do_guild(s, extra, server_id=20):
    now = datetime.datetime.now() - datetime.timedelta(hours=5)
    if extra.get("guild") != now.strftime("%Y-%m-%d-"):
        extra["guild"] = now.strftime("%Y-%m-%d")
        # join
        instructure = GUILD_ID.get(server_id)
        if not instructure:
            return True
        s.sendall(instructure)
        #time.sleep(10)
        #heart_beat(s)
        read_all(s)
        # visit famous
        for i in range(0, 10):
            s.sendall(b"\x00\x00\x00\x08\x00\x12\x00\x00\x00\x00\x47\x01")
            s.sendall(b"\x00\x00\x00\x07\x00\x13\x00\x00\x00\x00\x48")
        read_all(s)
        # donate coin
        for i in range(0, 5):
            s.sendall(b"\x00\x00\x00\x08\x00\x0b\x00\x00\x00\x00\x3a\x01")
        read_all(s)
        # guild signup
        s.sendall(b"\x00\x00\x00\x07\x00\x05\x00\x00\x00\x00\x3b")
        read_one(s)
        time.sleep(0.5)
        # guild mission reward
        s.sendall(b"\x00\x00\x00\x09\x00\x06\x00\x00\x00\x00\x3d\x03\x00")
        read_one(s)
        time.sleep(0.5)
        # donate reward
        s.sendall(b"\x00\x00\x00\x09\x00\x07\x00\x00\x00\x00\x3d\x02\x00")
        read_one(s)
        time.sleep(0.5)

        # reward 25, 50
        s.sendall(b"\x00\x00\x00\x08\x00\x08\x00\x00\x00\x00\x3c\x01")
        read_one(s)
        time.sleep(0.5)
        s.sendall(b"\x00\x00\x00\x08\x00\x09\x00\x00\x00\x00\x3c\x02")
        read_one(s)

        # see guild shop
        try:
            s.sendall(b"\x00\x00\x00\x07\x00\x0a\x00\x00\x00\x00\x45")
            while True:
                try:
                    head, body = read_one(s)
                    if head == b'\x00\x00\x00\x97':
                        break
                except:
                    break
            buy_succ = False
            if head == b'\x00\x00\x00\x97':
                # see shop and buy
                tobuy = []
                for i in range(0, 6):
                    item = body[i*23+4:i*23+4+23]
                    item_id = item[:4]
                    currency = item[17]
                    price = int.from_bytes(item[18:], byteorder='little')
                    if currency == 1 or (currency == 14 and price <= 200):
                        tobuy.append(item_id)
                if len(tobuy) >= 2:
                    for item in tobuy[:2]:
                        s.sendall(b"\x00\x00\x00\x0f\x00\x0a\x00\x00\x00\x00\x44" + item + b"\x00\x00\x00\x00")
                    # buy reward
                    s.sendall(b"\x00\x00\x00\x09\x00\x0b\x00\x00\x00\x00\x3d\x05\x00")
                    # reward 75
                    s.sendall(b"\x00\x00\x00\x08\x00\x0b\x00\x00\x00\x00\x3c\x03")
                    buy_succ = True
                else:
                    raise
            s.sendall(b"\x00\x00\x00\x07\x00\x08\x00\x00\x00\x00\x45")
            time.sleep(1)
            s.sendall(b"\x00\x00\x00\x07\x00\x08\x00\x00\x00\x00\x45")
            time.sleep(1)
            # shop refresh reward
            s.sendall(b"\x00\x00\x00\x09\x00\x0b\x00\x00\x00\x00\x3d\x04\x00")

            if buy_succ:
                # reward 100
                s.sendall(b"\x00\x00\x00\x08\x00\x0b\x00\x00\x00\x00\x3c\x04")
            else:
                # reward 75
                s.sendall(b"\x00\x00\x00\x08\x00\x0b\x00\x00\x00\x00\x3c\x03")

        except:
            import traceback
            print(traceback.format_exc())
            print("guild shop error!")



        read_all(s)
        # leave guild
        print("leave guild")
        s.sendall(b"\x00\x00\x00\x07\x00\x0f\x00\x00\x00\x00\x30")
        read_all(s)
        heart_beat(s)
        if not read_one(s):
            raise BaseException("bug guild account")
        return True


def draw_card(s):
    times = GOLD_WINE
    print("draw",times,"times")
    for turn in range(times):
        idx = (turn + 19).to_bytes(2, byteorder="big")
        s.sendall(b"\x00\x00\x00\x09" + idx + b"\x00\x00\x00\x00\xa3\x02\x00")


def achievement_reward(s, extra):
    if not extra.get("achievement"):
        print("do achievement")
        # 乱世英雄 10, 12, 15, 18, 20, 25
        for idx, item in enumerate([10, 12, 15, 18, 20, 25]):
            turn = (idx + 22).to_bytes(2, byteorder="big")
            code = (idx + 1).to_bytes(1, byteorder="big")
            s.sendall(b"\x00\x00\x00\x09" + turn + b"\x00\x00\x00\x01\x03\x01" + code)
        # 南征北战 ch3, ch4
        for idx, item in enumerate(["ch3", "ch4"]):
            turn = (idx + 28).to_bytes(2, byteorder="big")
            code = (idx + 1).to_bytes(1, byteorder="big")
            s.sendall(b"\x00\x00\x00\x09" + turn + b"\x00\x00\x00\x01\x03\x03" + code)
        extra["achievement"] = True
        return True

def seven_day(s, extra):
    if not extra.get("seven_day"):
        extra["seven_day"] = True
        s.sendall(b"\x00\x00\x00\x0f\x00\x26\x00\x00\x00\x01\x01\x01\x00\x00\x00\x01\x00\x00\x00")  # day1 1-1
        s.sendall(b"\x00\x00\x00\x0f\x00\x27\x00\x00\x00\x01\x01\x02\x00\x00\x00\x01\x00\x00\x00")  # day1 1-2

        s.sendall(b"\x00\x00\x00\x0f\x00\x28\x00\x00\x00\x01\x01\x01\x00\x00\x00\x02\x00\x00\x00")  # day2 1-1
        s.sendall(b"\x00\x00\x00\x0f\x00\x29\x00\x00\x00\x01\x01\x02\x00\x00\x00\x02\x00\x00\x00")  # day2 1-2

        s.sendall(b"\x00\x00\x00\x0f\x00\x2a\x00\x00\x00\x01\x01\x01\x00\x00\x00\x03\x00\x00\x00")  # day3 1-1
        s.sendall(b"\x00\x00\x00\x0f\x00\x2b\x00\x00\x00\x01\x01\x02\x00\x00\x00\x03\x00\x00\x00")  # day3 1-2

        s.sendall(b"\x00\x00\x00\x0f\x00\x2c\x00\x00\x00\x01\x01\x01\x00\x00\x00\x04\x00\x00\x00")  # day4 1-1
        s.sendall(b"\x00\x00\x00\x0f\x00\x2d\x00\x00\x00\x01\x01\x01\x00\x00\x00\x05\x00\x00\x00")  # day5 1-1
        s.sendall(b"\x00\x00\x00\x0f\x00\x2e\x00\x00\x00\x01\x01\x01\x00\x00\x00\x06\x00\x00\x00")  # day6 1-1
        s.sendall(b"\x00\x00\x00\x0f\x00\x2f\x00\x00\x00\x01\x01\x01\x00\x00\x00\x07\x00\x00\x00")  # day7 1-1
        return True

def update_extra(table_name, email, extra, c):
    c.execute("UPDATE "+table_name+" SET extra=? WHERE email=?", (json.dumps(extra), email))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser()
    parser.add_argument("email", help="login account")
    parser.add_argument("server_id", help="login server id", type=int)
    args = parser.parse_args()
    email = args.email
    server_id = args.server_id

    server = SERVER_LIST[server_id]
    SERVERID, HOST, PORT = server
    # sql connection
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    table_name = 'pigs_{}'.format(server_id)
    c.execute("SELECT extra FROM " + table_name + " WHERE email=?", (email, ))
    row = c.fetchone() or [dict()]
    extra = row[0]
    try:
        extra = json.loads(extra)
    except:
        extra = dict()

    device_id = make_imei()
    if "token" in extra and "user_id" in extra:
        try:
            token = extra["token"]
            user_id = extra["user_id"]
            session = login_verify(user_id, token, version=version, server_id=SERVERID)
        except:
            #token, user_id = create_account(email, device_id)
            token, user_id = login_account(email, device_id)
            session = login_verify(user_id, token, version=version, server_id=SERVERID)
    else:  # new account
        token, user_id = create_account(email, device_id)
        session = login_verify(user_id, token, version=version, server_id=SERVERID)
    extra["token"] = token
    extra["user_id"] = user_id
    update_extra(table_name, email, extra, c)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(make_login_server_data(version, user_id, SERVERID, device_id, session, os="Android OS 6.0.1 / API-23 (V417IR/eng.root.20181010.162559)", phone="Netease MuMu"))
        head, body = read_one(s)
        r = init_data(body)
        read_all(s)
        heart_beat(s)
        s.sendall(b"\x00\x00\x00\x07\x00\x0f\x00\x00\x00\x00\x30")
