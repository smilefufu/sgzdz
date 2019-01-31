#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import asyncio
import socket
import sqlite3
import json
import sys

import aiohttp
import requests

import socks
from lib import make_logon_data, get_proxies, del_proxy, make_send_msg_data, make_bad_msg_data

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
    print(r)
    return r['uid'], r['token']

async def login_verify(user_id, token, version='1.5.60090', proxy=None):
    # return tcp session
    url = 'http://sgz-login.fingerfunol.com:30006/entry_server/login_verify?version=%s&server_id=20&userid=%s&channel=4&session=%s&platform=a8card&isdebug=False&activation_code=' % (version, user_id, token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, proxy=proxy, timeout=5) as resp:
            t = await resp.text()
            r = json.loads(t)
    print(r)
    return r['session']

async def one(email):
    """maintance one guard"""
    proxies = get_proxies()
    imei = "".join(str(random.randint(0,9)) for x in range(1, len("863272039030961")+1))
    version = "1.5.60090"
    uid, token, session = None, None, None
    asyncio.sleep(random.randint(0,5))
    while True:
        print("start:", email)
        #random.shuffle(proxies)
        #host, port = proxies[0]
        #http_proxy = "http://{}:{}".format(host, port)
        http_proxy = None
        try:
            if not uid or not token:
                print("get uid, token", email)
                uid, token = await user_do(email, imei)
            if not session:
                print("get session", email)
                session = await login_verify(uid, token, version=version)

#            socks.set_default_proxy(socks.HTTP, host, int(port))
            print("try connect to server", email)
            fut = asyncio.open_connection('128.14.230.246', 30000)
            reader, writer = await asyncio.wait_for(fut, timeout=3)
            writer.write(make_logon_data(version, uid, imei, session))
            writer.write(b'\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x07\x00\x01\x00\x00\x00\x00\x07')    # seems like 2 cmd, each len is 7, read on screen players?  00 00 00 00 00 00 05 an
            head = await reader.read(4)
            body_len = int.from_bytes(head, byteorder="big")
            body = b""
            while len(body) < body_len:
                body += await reader.read(body_len - len(body))
            writer.write(b'\x00\x00\x00\x02\x01\x00')  # heartbeat?
            print("get body len", body_len, ":", body)
            print("---------------do something----------------")
            # writer.write(make_send_msg_data("早上好", 352131, 3))
            # writer.write(make_send_msg_data("中午好", 352131, 3))
            # writer.write(make_send_msg_data("晚上好", 352131, 3))
            #print("sending bomb...")
            #for i in range(0, 1000):
            #    payload = b""
            #    for i in range(random.randint(1, 100)):
            #        payload += random.randint(0,255).to_bytes(1, byteorder="big")
            #        writer.write(make_bad_msg_data(payload, 352131, 3+i))
            #writer.write(make_bad_msg_data(b'aaaa' + b'\xe2\x80\x8e\xe2\x80\x8f'*30 + b'bbbbb', 352131, 3))
            #writer.write(make_bad_msg_data(b'a'*255, 352131, 3))
            #writer.write(make_send_msg_data('\ufdf0\ufdd0\ufd90\ufd86', 352131, 3))
            #print("sent!")
            receiver = 358864
            while True:
                writer.write(make_send_msg_data('巴巴拉小魔仙!', receiver, 3))
                # read packages and do nothing
                head = await reader.read(4)
                body_len = int.from_bytes(head, byteorder="big")
                body = b""
                while len(body) < body_len:
                    body += await reader.read(body_len - len(body))
                print("get body len", body_len, ":", body)
                await asyncio.sleep(10)
                rd = lambda : random.randint(0,255).to_bytes(1, byteorder='big')
                # writer.write(b"\x00\x00\x00\x0e\x01\x01\xf0\x7b\x05" + rd() + rd() + rd() + rd() + rd() + rd() + rd() + rd() + b"\x42")
                writer.write(b'\x00\x00\x00\x02\x01\x00')  # heartbeat?
        except BrokenPipeError:
            print("disconnected!!!")
            # uid = token = session = None
        except:
            import traceback
            print(traceback.format_exc())

if __name__ == "__main__":
    print(sys.argv)
    loop = asyncio.get_event_loop()
    guards = []
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    c.execute("SELECT * FROM guards ORDER BY RANDOM() LIMIT 1")
    for row in c.fetchall():
        guards.append(one(row[0]))
    loop.run_until_complete(asyncio.gather(*guards))
    loop.close()
