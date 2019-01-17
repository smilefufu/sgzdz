#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import asyncio
import socket
import sqlite3
import json

import aiohttp
import requests

import socks
from lib import make_logon_data, get_proxies, del_proxy

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 9.0.1; en-us;) AppleWebKit/533.1 (KHTML, like Gecko) Version/5.0 Mobile Safari/533.1"
}
socket.socket = socks.socksocket

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
    print(r)
    return r['uid'], r['token']

async def login_verify(user_id, token, version='1.4.58672', proxy=None):
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
    version = "1.4.58672"
    uid, token, session = None, None, None
    asyncio.sleep(random.randint(0,5))
    while True:
        print("start:", email)
        random.shuffle(proxies)
        host, port = proxies[0]
        http_proxy = "http://{}:{}".format(host, port)
        try:
            if not uid or not token:
                print("get uid, token", email)
                uid, token = await user_do(email, imei, proxy=http_proxy)
            if not session:
                print("get session", email)
                session = await login_verify(uid, token, version=version, proxy=http_proxy)

            socks.set_default_proxy(socks.HTTP, host, int(port))
            print("try connect to server", email)
            fut = asyncio.open_connection('128.14.230.246', 30000)
            reader, writer = await asyncio.wait_for(fut, timeout=3)
            writer.write(make_logon_data(version, uid, imei, session))
            writer.write(b'\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x07\x00\x01\x00\x00\x00\x00\x07')    # seems like 2 cmd, each len is 7, read on screen players?  00 00 00 00 00 00 05 an
            writer.write(b'\x00\x00\x00\x02\x01\x00')  # heartbeat?
            while True:
                # read packages and do nothing
                r = await reader.read(-1)
                await asyncio.sleep(3)
                writer.write(b'\x00\x00\x00\x02\x01\x00')  # heartbeat?
        except:
            import traceback
            print(traceback.format_exc())
            proxies = proxies[1:]
            del_proxy(host)
            socks.set_default_proxy()
            if len(proxies) == 0:
                proxies = get_proxies()
                print("get new proxies:", len(proxies))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    guards = []
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    c.execute("SELECT * FROM guards ORDER BY random() LIMIT 1")
    for row in c.fetchall():
        guards.append(one(row[0]))
    loop.run_until_complete(asyncio.gather(*guards))
    loop.close()
