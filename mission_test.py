#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import socket
import sys
import time
from functools import reduce

import requests

from lib import login_verify, create_role, make_data, find_cards, get_formation, body_test, make_battle_data, init_data, gen_name, make_story_data, make_login_server_data
from const import EPISODES

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
        except socket.timeout:
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
            #cards = find_cards(body)
            #if cards:
            #    print("CARDS:", CARDS)
            #    print("cards:", cards)
            #    CARDS.update(cards)
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
    else:
        s.send(b'\x00\x00\x00\x07\x00\x04\x00\x00\x00\x00\x06')
        for episode in sp[1:]:
            battle_episode(s, episode)

if __name__ == "__main__":
    version = '1.5.60090'
    # socket.socket = socks.socksocket
    server = (20, '128.14.230.246', 30000)
    # server = (18, '128.14.230.114', 30000)
    SERVERID, HOST, PORT = server
    # with open("proxy.txt", "r") as f:
    #     proxies = f.readlines()
    # conn = sqlite3.connect("data.db")
    # conn.isolation_level = None   # auto commit
    # c = conn.cursor()
    # c.execute("CREATE TABLE IF NOT EXISTS alts (email varchar unique, name varchar unique, role_id int)")
    # random.shuffle(proxies)
    # host, port = proxies[0].strip().split()
    # http_proxy = "http://{}:{}".format(host, port)
    email = sys.argv[1]
    device_id = make_imei()
    print("login account:", email)
    token, user_id = create_account(email, device_id)
    #token, user_id = login_account(email, device_id)
    session = login_verify(user_id, token, version=version, server_id=SERVERID)
    print("creating role")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        #s.send(make_logon_data(version, user_id, device_id, session))
        s.send(make_login_server_data(version, user_id, SERVERID, device_id, session))
        head, body = read_one(s)
        r = init_data(body)
        cards = r['cards']
        if cards:
            CARDS.update(cards)
            CARDS
        print('init:', r)
        if not "name" in r:
            # need create role
            print(r)
            role_id, name = create_role(s, gen_name(seed=r["role_id"]))
            print(role_id, name)
        read_all(s)
        chapter, section = r['story_index']
        left_chapters = EPISODES[chapter-1:]
        left_story = reduce(lambda t, c: t+c, left_chapters, [])[section-1:]
        for story in left_story:
            do_story(s, story)
        exit()

        s.send(make_story_data(1))
        while True:
            try:
                head, body = read_one(s)
                print("get pack", head)
                if head in (b'\x00\x00\x00\x85', b'\x00\x00\x00\xb1'): # and body.startswith(b'\x01\x00\x27'):
                    body
                    card_id = body[3:11]
                    card_code = body[11:15]  # should be: fc 32 01 00
                    card_code
                    CARDS.add(('zumao', card_id))
                    break
            except:
                print("SOME THING BAD HAPPEN")
                exit()
        s.send(make_story_data(2))
        battle_episode(s, '1-1')
        s.send(make_story_data(3))
        s.send(make_story_data(4))
        battle_episode(s, '1-2')
        s.send(make_story_data(5))
        s.send(make_story_data(6))
        s.send(make_story_data(7))
        s.send(make_story_data(8))
        s.send(make_story_data(9))
        s.send(make_story_data(10))
        battle_episode(s, '1-3')
        exit()

        if r["story_index"] <= 1:
            s.send(make_data("zumao"))
            head, body = read_one(s)
            print(head, body)
            r = body_test(body)
            print(r)
            CARDS.add(r['args']['card'])

        s.send(make_data("huangjin"))
        read_all(s)
        s.send(make_battle_data(CARDS, '1-1'))
        read_all(s)
        time.sleep(10)
        s.send(b'\x00\x00\x00\x02\x01\x00')
        s.send(make_data("first_battle_end"))
        read_all(s)
