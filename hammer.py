#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import math
import random
import socket
import time
import json
import datetime
import argparse
import sqlite3
from functools import reduce

import requests

from lib import login_verify, create_role, make_data, get_formation, body_test, make_battle_data, gen_name, make_login_server_data, make_quick_battle_data, init_data
from const import EPISODES, SERVER_LIST, GUILD_ID, CARD_CODE_PURPLE, CARD_CODE_GOLD

BAD_CARD = ['曹仁']

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
    if head == b"\x00\x00\x00\x09" and body.startswith(b"\x01\x00\x5c\x01\x0d"):  # 元宝
        GOLD = int.from_bytes(body[-4:], byteorder="little")
        print("gold change:", GOLD)
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

class SGZDZ(object):

    def __init__(self, email, server_id, version="1.7.61848", token=None, user_id=None):
        self._email = email
        self._server_id = server_id
        self._device_id = make_imei()
        self._token = token
        self._user_id = user_id
        self._version = version
        self.__counter = 1
        i = 0
        while i < 3:
            try:
                self.connect()
                break
            except:
                i += 1
                print("error on first pack! Retry", i, "on email", email)

    def connect(self):
        self._heartbeat = time.time()
        server = SERVER_LIST[self._server_id]
        SERVERID, HOST, PORT = server
        try:
            if self._token and self._user_id:
                session = login_verify(self._user_id, self._token, version=self._version, server_id=SERVERID)
            else:
                raise BaseException("go except")
        except:
            assert self._email, "Not supported login method!"
            self._token, self._user_id = login_account(self._email, self._device_id)
            session = login_verify(self._user_id, self._token, version=self._version, server_id=self._server_id)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((HOST, PORT))
        self._sock.sendall(make_login_server_data(self._version, self._user_id, SERVERID, self._device_id, session, os="Android OS 6.0.1 / API-23 (V417IR/eng.root.20181010.162559)", phone="Netease MuMu"))
        head, body = self.read_one()
        self._info = init_data(body)
        self._gold = self._info["gold"]
        self._purple_cards = self._info["purple_cards"]
        self._gold_cards = self._info["gold_cards"]
        self._market = self._info["market"]
        self._market_id_map = dict()  # key: market_id, value: card_id
        self.read_all()
        heart_beat(self._sock)
        print("login", self._email, "success!")

    def close(self):
        self._sock.close()
        try:
            conn = sqlite3.connect("data.db")
            conn.isolation_level = None   # auto commit
            c = conn.cursor()
            table_name = 'pigs_{}'.format(self._server_id)
            c.execute("UPDATE " + table_name + " SET gold=? WHERE email=?", (self._gold, self._email))
        except:
            pass

    def read_all(self):
        while True:
            try:
                pack = self.read_one()
                if not pack:
                    return True
                head, body = pack
            except socket.timeout:
                self._sock.settimeout(None)
                return True

    def read_one(self):
        head = read_bytes(self._sock, 4)
        if not head:
            return None
        body = read_bytes(self._sock, int.from_bytes(head, byteorder="big"))
        if head == b"\x00\x00\x00\x09" and body.startswith(b"\x01\x00\x5c\x01\x0d"):  # 元宝
            self._gold = int.from_bytes(body[-4:], byteorder="little")
            print(self._email, "gold change:", self._gold)
        return head, body

    def _send_data(self, data):
        # send data, auto change pack count
        if time.time() - self._heartbeat >= 10:
            heart_beat(self._sock)
            self._heartbeat = time.time()
        pid = self.__counter.to_bytes(2, byteorder='big')
        self._sock.sendall(data[:4] + pid + data[6:])
        self.__counter += 1
        return pid

    def _read_until(self, head, body_start, max_read=10):
        assert head or body_start
        c = max_read
        while c > 0:
            if time.time() - self._heartbeat >= 10:
                heart_beat(self._sock)
                self._heartbeat = time.time()
            try:
                h, b = self.read_one()
                # print(h, b)
            except:
                continue
            if (h == head or head is None) and (body_start is None or b.startswith(body_start)):
                return b
            c -= 1
        return None

    def _read_pid(self, pid, max_read=10):
        """read with package id"""
        c = max_read
        while c > 0:
            if time.time() - self._heartbeat >= 10:
                heart_beat(self._sock)
                self._heartbeat = time.time()
            h, b = self.read_one()
            if b.startswith(pid):
                return b
            c -= 1
        return None

    def query_price(self, card_id):
        data = b"\x00\x00\x00\x0f\x00\x05\x00\x00\x00\x00\x93" + card_id
        self.read_all()
        pid = self._send_data(data)
        body = self._read_pid(pid)
        if body:
            price_data = body[6:10]
            return int.from_bytes(price_data, byteorder='little')
        else:
            return None

    def put_market(self, card_id, price):
        self.query_price(card_id)
        data = b"\x00\x00\x00\x1b\x00\x0b\x00\x00\x00\x00\x94\x00\x00\x00\x00"
        data += card_id
        data += b"\x01\x00\x00\x00"
        data += price.to_bytes(4, byteorder='little')
        self._send_data(data)
        body = self._read_until(None, b"\x01\x00\x59", max_read=10)
        market_id = body[3:3+8]
        self._market_id_map[market_id] = card_id
        return market_id

    def sell(self, amount, can_over=True):
        # can_over: can over the amount
        cards_can_sell = list()
        for card_name, card_id, cd in self._gold_cards + self._purple_cards:
            if card_name in BAD_CARD or card_id[4:] != b"\x00\x00\x00\x00" or cd:
                continue
            price = self.query_price(card_id)
            cards_can_sell.append((card_name, card_id, price))
        # TODO: find the best way to form the price
        selling_cards = list()
        need_amount = amount
        for card_name, card_id, price in cards_can_sell:
            if need_amount > 10 * price:
                price_to_put = 10 * price
            elif need_amount >= price/2:
                base = int(price/2)
                step = int(price/10)
                times = math.ceil((need_amount - base)/step) if can_over else math.floor((need_amount - base)/step)
                price_to_put = base + step * times
            else:
                print("price less than limit price, need_amount:", need_amount)
                continue
            try:
                market_id = self.put_market(card_id, price_to_put)
            except:
                print("put market fail", card_id)
                continue
            selling_cards.append((card_name, card_id, price_to_put, market_id))
            need_amount -= price_to_put
            if need_amount <= 0:
                break
        return selling_cards

    def buy(self, market_id):
        # len(market_id) == 8
        data = b"\x00\x00\x00\x0f\x00\x1c\x00\x00\x00\x00\x95"
        data += market_id
        pid = self._send_data(data)
        self.read_all()
        return pid

    def smash(self):
        for i in range(8):
            self._sock.sendall(b"\x00\x00\x00\x07\x00\x01\x00\x00\x00\x00\xd2")
        self.read_all()

    def harvest(self, market_id):
        data = b"\x00\x00\x00\x0f\x00\x1c\x00\x00\x00\x00\x98"
        data += market_id
        pid = self._send_data(data)
        self.read_all()
        if market_id in self._market_id_map:
            # change cards list
            sold_card_id = self._market_id_map[market_id]
            for card in self._purple_cards[:]:
                card_name, card_id, cd = card
                if card_id == sold_card_id:
                    self._purple_cards.remove(card)
                    break
            for card in self._gold_cards[:]:
                card_name, card_id, cd = card
                if card_id == sold_card_id:
                    self._gold_cards.remove(card)
                    break
        return pid

    def cancel_sell(self, market_id):
        data = b"\x00\x00\x00\x0f\x00\x07\x00\x00\x00\x00\x96"
        data += market_id
        self._send_data(data)
        self.read_all()


def do(buyer, smasher, server_id):
    smashapp = SGZDZ(smasher, server_id)
    card_list = smashapp.sell(41180)
    buyapp = SGZDZ(buyer, server_id)
    if sum(x[2] for x in card_list) <= 41180:
        raise BaseException("ERROR: not enough card for trade!!!")
    for card in card_list:
        print(card)
        card_name, card_id, price_to_put, market_id = card
        buyapp.buy(market_id)
        smashapp.harvest(market_id)
    smashapp.smash()
    print("smasher gold:", smashapp._gold, "buyer gold:", buyapp._gold)
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    table_name = 'pigs_{}'.format(server_id)
    c.execute("UPDATE " + table_name + " SET gold=? WHERE email=?", (smashapp._gold, smasher))
    c.execute("UPDATE " + table_name + " SET gold=? WHERE email=?", (buyapp._gold, buyer))
    return buyapp._gold, smashapp._gold

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("buyer", help="gold provider email")
    parser.add_argument("smasher", help="pig smasher email")
    parser.add_argument("server_id", help="login server id", type=int)
    args = parser.parse_args()
    buyer = args.buyer
    smasher = args.smasher
    server_id = args.server_id

    smashapp = SGZDZ(smasher, server_id)
    card_list = smashapp.sell(41180)
    buyapp = SGZDZ(buyer, server_id)
    if sum(x[2] for x in card_list) < 41180:
        print("ERROR: not enough card for trade!!!")
        exit()
    for card in card_list:
        print(card)
        card_name, card_id, price_to_put, market_id = card
        buyapp.buy(market_id)
        smashapp.harvest(market_id)
    smashapp.smash()
    print("smasher gold:", smashapp._gold, "buyer gold:", buyapp._gold)
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    table_name = 'pigs_{}'.format(server_id)
    c.execute("UPDATE " + table_name + " SET gold=? WHERE email=?", (smashapp._gold, smasher))
    c.execute("UPDATE " + table_name + " SET gold=? WHERE email=?", (buyapp._gold, buyer))
