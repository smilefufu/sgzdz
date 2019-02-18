#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import socket
import sys
import time
import datetime
import argparse
import sqlite3
from functools import reduce

import requests

from lib import login_verify, create_role, make_data, get_formation, body_test, make_battle_data, init_data, gen_name, make_login_server_data, make_quick_battle_data
from const import EPISODES, SERVER_LIST

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 9.0.1; en-us;) AppleWebKit/533.1 (KHTML, like Gecko) Version/5.0 Mobile Safari/533.1"
}

CARDS = set()

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
    # print(logon_data)
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
            head = read_bytes(s, 4)
            if not head:
                break
            body = read_bytes(s, int.from_bytes(head, byteorder="big"))
            if not body:
                break
        except socket.timeout:
            s.settimeout(None)
            print("all data received!")
            break

def read_one(s):
    head = read_bytes(s, 4)
    if not head:
        return None
    body = read_bytes(s, int.from_bytes(head, byteorder="big"))
    return head, body

def battle_episode(s, episode):
    s.send(make_battle_data(CARDS, episode))
    #read_all(s)
    #time.sleep(10)
    s.send(b'\x00\x00\x00\x02\x01\x00')
    s.send(make_data("first_battle_end"))
    read_all(s)

def do_story(s, story):
    print("do story:", story)
    sp = story.split()
    if len(sp) == 1:
        # no battle, but card is possible
        s.send(b'\x00\x00\x00\x07\x00\x04\x00\x00\x00\x00\x03')
        # try not find any card
        return 0
    else:
        s.send(b'\x00\x00\x00\x07\x00\x04\x00\x00\x00\x00\x06')
        times = 0
        for episode in sp[1:]:
            battle_episode(s, episode)
            times += 1
        return times

def do_attend(s):
    s.send(b'\x00\x00\x00\x07\x00\x02\x00\x00\x00\x00\xc7')



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser()
    parser.add_argument("email", help="login account")
    parser.add_argument("server_id", help="login server id", type=int)
    args = parser.parse_args()
    email = args.email
    server_id = args.server_id
    version = '1.5.60090'

    server = SERVER_LIST[server_id]
    SERVERID, HOST, PORT = server
    # sql connection
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    table_name = 'pigs_{}'.format(server_id)

    device_id = make_imei()
    print("login account:", email)
    token, user_id = create_account(email, device_id)
    #token, user_id = login_account(email, device_id)
    session = login_verify(user_id, token, version=version, server_id=SERVERID)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.send(make_login_server_data(version, user_id, SERVERID, device_id, session))
        head, body = read_one(s)
        r = init_data(body)
        if datetime.datetime.now().hour == 3:  # 3 o'clock do daily
            sql = "UPDATE {} SET level=? WHERE email=?".format("pigs_"+str(SERVERID))
            c.execute(sql, (r['level'], email))
            do_attend(s)
            # get lastday food
            s.send(b'\x00\x00\x00\x0c\x00\x05\x00\x00\x00\x01\x3d\x00\x03\x01\x02\x03')
        cards = r['cards']
        if cards:
            CARDS.update(cards)
        print('init:', r)
        read_all(s)
        if not "name" in r:
            # need create role
            role_id, name = create_role(s, gen_name(seed=r["role_id"]))
            print('created role:', role_id, name)
        chapter, section = r['story_index']
        left_chapters = EPISODES[chapter-1:]
        left_story = reduce(lambda t, c: t+c, left_chapters, [])[section-1:]
        battle_times = 0
        for story in left_story:
            battle_times += do_story(s, story)
            if (r['level'] > 5 and battle_times >= 20) or battle_times >= 25:  # 100/5 = 20 maxed battle times, stamina empty
                break
        if battle_times < 20:  # need shaodang
            time_section = int(datetime.datetime.now().hour / 8)
            chapter = time_section + 1
            section = 1
            print('start shao dang')
            for i in range(20):
                s.send(make_quick_battle_data(chapter, section))
        # update info
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = "UPDATE {} SET level = ?, last_login=? WHERE email=?".format(table_name)
        c.execute(sql, (r['level'], now, email))
        exit()
