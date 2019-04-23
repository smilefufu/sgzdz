#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import asyncio
import socket
import sqlite3
import json
import sys
import datetime
import traceback

import aiohttp
import requests

import socks
from lib import make_logon_data, init_data, decode_players

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 9.0.1; en-us;) AppleWebKit/533.1 (KHTML, like Gecko) Version/5.0 Mobile Safari/533.1"
}

accounts = [
    dict(email="guyuena001@gmail.com", role_id=357635, name='祁國偉', status="offline"),
    dict(email="guyuena002@gmail.com", role_id=358815, name='2囧2'),
    dict(email="guyuena003@gmail.com", role_id=358820, name='iPhone'),
    dict(email="guyuena004@gmail.com"),
    dict(email="guyuena005@gmail.com"),
    dict(email="guyuena006@gmail.com"),
    dict(email="guyuena007@gmail.com"),
    dict(email="guyuena008@gmail.com"),
    dict(email="guyuena009@gmail.com"),
    dict(email="guyuena010@gmail.com"),
    dict(email="guyuena011@gmail.com"),
    dict(email="guyuena012@gmail.com"),
    dict(email="guyuena013@gmail.com"),
    dict(email="guyuena014@gmail.com"),
    dict(email="guyuena015@gmail.com"),
    dict(email="guyuena016@gmail.com"),
    dict(email="guyuena017@gmail.com"),
    dict(email="guyuena018@gmail.com"),
    dict(email="guyuena019@gmail.com"),
    dict(email="guyuena020@gmail.com"),
]

tmp = dict()

def is_gyn(role_id):
    info = tmp.get(role_id, None)
    if not info:
        print("no detail info!")
        return False
    else:
        if info["level"]>=30 and info["model"] == 5 and info["atk"]<25000:
            return True
        if info["level"]>=35 and info["vip"] < 3 and info["atk"] < 40000:
            return True
        if info["name"].isdigit() and (info["name"][:2] in ("18", "19", "20", "21") or len(info["name"]) == 4):
            return True
    return False

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
            return

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


async def one(loop, email):
    """maintance one account"""
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    imei = "".join(str(random.randint(0,9)) for x in range(1, len("863272039030961")+1))
    version = "1.7.61848"
    for account in accounts:
        if account["email"] == email:
            account["status"] = "online"
            break
    uid = account.get("uid", None)
    token = account.get("token", None)
    print("starting:", email)
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
        print(email, r)
        account["role_id"] = r["role_id"]

        writer.write(b'\x00\x00\x00\x02\x01\x00')
        writer.write(b'\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x07\x00\x01\x00\x00\x00\x00\x07')
        writer.write(b'\x00\x00\x00\x0e\x01\x01\x9f\x79\x05\x00\xf0\x1c\xf6\xc1\xab\x77\xd1\x41')
        asyncio.ensure_future(heartbeat(writer), loop=loop)
        need_check = True
        while True:
            head, body = await read_one(reader)
            players = decode_players(body)
            now = "[{}]".format(datetime.datetime.now().strftime("%Y-%m-%d %T"))
            if players:
                if len(players) > 1:
                    # check whether entered in same district
                    print(accounts)
                    online_role_id = [x["role_id"] for x in accounts if x.get("status") == "online"]
                    for player in players:
                        name, level, gender, role_id = player
                        if r["role_id"] != role_id and role_id in online_role_id:
                            # can see other monitor account
                            # close and quit
                            writer.close()
                            account["status"] = "offline"
                            print("same area, offline!", role_id)
                            return

                    # start do things with server
                    for player in players:
                        name, level, gender, role_id = player
                        if role_id not in tmp:
                            # read detail
                            writer.write(b"\x00\x00\x00\x0b\x00\x81\x00\x00\x00\x00\xda" + role_id.to_bytes(4, byteorder='little'))
                elif len(players) == 1:
                    name, level, gender, role_id = players[0]
                    info = tmp.get(role_id, None)
                    if info:
                        print(now, role_id, info["name"], "is online")
                        if tmp.get("gyn_status", None):
                            os.system("curl http://localhost:7788/target_online?role_id={} &".format(role_id))
                    else:
                        # not info, check database?
                        print(now, role_id, "online")
                        # TODO: if face a hard drive io performance problem, common the query below
                        c.execute("SELECT * FROM sbs WHERE role_id=?", (role_id, ))
                        if c.fetchone():
                            os.system("curl http://localhost:7788/target_online?role_id={} &".format(role_id))
                        writer.write(b"\x00\x00\x00\x0b\x00\x81\x00\x00\x00\x00\xda" + role_id.to_bytes(4, byteorder='little'))
            elif head == b'\x00\x00\x00\x07' and body.startswith(b'\x01\x00\x1b'):
                # offline
                role_id = int.from_bytes(body[-4:], byteorder="little")
                info = tmp.get(role_id, None)
                if info:
                    print(now, role_id, info["name"], "is offline")
                    if tmp.get("gyn_status", None):
                        os.system("curl http://localhost:7788/target_offline?role_id={} &".format(role_id))
                else:
                    print(now, role_id, "offline")
            elif body.startswith(b"\x00\x81\x00\x00\x00\x00"):
                # click player return pack
                try:
                    role_id = int.from_bytes(body[6:10], byteorder="little")
                    name_len = body[12]
                    name = body[13:13+name_len].decode("utf8")
                    model_id = body[13+name_len]
                    level = body[14+name_len]
                    vip = body[15+name_len]
                    atk = int.from_bytes(body[16+name_len: 20+name_len], byteorder='little')
                    guild_len = body[29+name_len]
                    guild = None if guild_len == 0 else body[30+name_len:].decode('utf8')
                    tmp[role_id] = dict(name=name, model=model_id, level=level, vip=vip, atk=atk, guild=guild)
                    gyn_status = is_gyn(role_id)
                    if gyn_status:
                        c.execute("SELECT * FROM pigs_20 WHERE role_id=?", (role_id, ))
                        if not c.fetchone():
                            # not myself
                            os.system("curl http://localhost:7788/target_online?role_id={} &".format(role_id))
                            c.execute("REPLACE INTO sbs (name, level, role_id, model, atk, vip) VALUES (?,?,?,?,?,?)", (name, level, role_id, model_id, atk, vip))
                            tmp["gyn_status"] = gyn_status
                            print(now, role_id, gyn_status, tmp[role_id])
                        else:
                            print(now, role_id, "self", tmp[role_id])
                    else:
                        print(now, role_id, is_gyn(role_id), tmp[role_id])
                        pass
                except:
                    print(traceback.format_exc())
            sys.stdout.flush()

    except BrokenPipeError:
        print("???", traceback.format_exc())
    except:
        print("wtf!!!!", traceback.format_exc())
    finally:
        account["status"] = "offline"


async def dispatcher(loop, interval=15*60):
    email = accounts[0]["email"]
    asyncio.ensure_future(one(loop, email), loop=loop)
    while True:
        await asyncio.sleep(interval)
        new_email = None
        for m in accounts:
            if m.get("status") != "online":
                new_email = m["email"]
                break
        asyncio.ensure_future(one(loop, new_email), loop=loop)
        print("now online accounts:", [x for x in accounts if x.get("status") == "online"])


if __name__ == "__main__":
    #target_ids, seconds = sys.argv[1:]
    #targets = list(map(int, target_ids.split(",")))
    #seconds = int(int(seconds)/2)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(dispatcher(loop))
    loop.close()
