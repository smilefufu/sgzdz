#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random
import socket
import time
import sys
import os
import  asyncio

from lib import user_do, login_verify, decode_readable_string, find_names, decode_players, save_names, record_player, is_target, body_test

version = '1.7.61848'
imei = "".join(str(random.randint(0,9)) for x in range(1, len("863272039030961")+1))
email = "fufu6@meirishentie.com" if len(sys.argv) == 1 else sys.argv[1]
user_id, token = user_do(email, imei, passwd="+KB9SfNXlNQ=")
session = login_verify(user_id, token, version)


def make_logon_data():
    package_data = b'\x09'
    package_data += bytes(version, 'utf8')
    package_data += b'\x14\x00\x04\x00\x07'
    package_data += b'a8_card'
    package_data += b'\x00\x20'
    package_data += bytes(user_id, 'utf8')
    package_data += b'\x0f'
    package_data += bytes(imei+';Android OS 6.0.1 / API-23 (V417IR/eng.root.20180103.167389)', 'utf8')
    package_data += b'\x0c'
    package_data += b'Netease MuMu@'
    package_data += b'\xac'
    package_data += bytes(session, 'utf8')
    logon_data = len(package_data).to_bytes(4, byteorder='big') + package_data
    # print(logon_data)
    return logon_data


def package_reader(s):
    buf = b""
    len_need = 4
    ret = []
    while True:
        if len(ret) == 0:  # get head first
            len_need = 4
        elif len(ret) == 1:
            head = ret[0]
            len_need = int.from_bytes(head, byteorder='big')
        else:
            data = dict(head=ret[0], body=ret[1])
            ret = []
            yield data
        while len(buf) < len_need:
            r = s.recv(1400)
            if not r:
                raise BaseException("get null data!!!")
            buf += r
        ret.append(buf[:len_need])
        buf = buf[len_need:]

async def send_heart_beat():
    global writer
    while not writer:
        print("wait writer")
        await asyncio.sleep(1)
    sent_logon = False
    while True:
        writer.write(b'\x00\x00\x00\x02\x01\x00')  # heartbeat?
        if not sent_logon:
            print("sending `get on screen players`")
            writer.write(b'\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x07\x00\x01\x00\x00\x00\x00\x07')    # seems like 2 cmd, each len is 7, read on screen players?  00 00 00 00 00 00 05 and 00 00 00 00 00 00 07
            sent_logon = True
        await asyncio.sleep(10)


async def read_packages():
    global reader
    global user_pool
    while not reader:
        print("wait reader")
        await asyncio.sleep(1)
    buf = b""
    bn_pool = set()
    pool_time = time.time()
    while True:

        # read one full package
        len_need = 4
        ret = []
        while True:
            if len(ret) == 0:  # get head first
                len_need = 4
            elif len(ret) == 1:
                head = ret[0]
                len_need = int.from_bytes(head, byteorder='big')
            else:
                head, body = ret
                break
            while len(buf) < len_need:
                r = await reader.read(1400)
                if not r:
                    raise BaseException("get null data!!!")
                buf += r
            ret.append(buf[:len_need])
            buf = buf[len_need:]

        if head in (b'\x00\x00\x00\x0f',  b'\x00\x00\x00\x03', b'\x00\x00\x00\x07'):
            # print('other players move instruction')
            if head == b'\x00\x00\x00\x07':
                role_id = int.from_bytes(body[-4:], byteorder="little")
                print(role_id, "offline")
                shl = 'curl "localhost:7788/offline?role_id={}" 1>>/dev/null 2>>/dev/null &'.format(role_id)
                os.popen(shl)
            continue
        r = body_test(body)
        if r and r["action"].startswith("guild"):
            print(r)
            role_id = r["args"]["role_id"]
            name = r["args"]["name"]
            user_pool.add((name, 30, '0', role_id))
            #shell = 'curl "localhost:7788/online?name={}&level={}&gender={}&role_id={}" 1>>/dev/null 2>>/dev/null &'.format(name, 30, 0, role_id)
            #os.popen(shell)
            continue
        # print("head:", head)
        # if int.from_bytes(head, byteorder='big') < 640000:
            # print("body:", body)
        readable_string = decode_readable_string(body)
        # print(readable_string)
        # names = find_names(readable_string)
        names = decode_players(body)
        if names:
            print(names)
        #    name, level, gender, role_id = names[0]
        #    if level > 20:
        #        record_player(names)
        if names and len(names) == 1:
            name, level, gender, role_id = names[0]
            if level >= 25:
                user_pool.add((name, level, gender, role_id))
                #shell = 'curl "localhost:7788/online?name={}&level={}&gender={}&role_id={}" 1>>/dev/null 2>>/dev/null &'.format(name, level, gender, role_id)
                #os.popen(shell)


reader, writer = None, None

async def init_connection():
    global reader
    global writer
    reader, writer = await asyncio.open_connection('128.14.230.246', 30000)
    writer.write(make_logon_data())

user_pool = set()
async def send_routin():
    global user_pool
    while True:
        await asyncio.sleep(1)
        while True:
            try:
                name, level, gender, role_id = user_pool.pop()
                shell = 'curl "localhost:7788/online?name={}&level={}&gender={}&role_id={}" 1>>/dev/null 2>>/dev/null &'.format(name, level, gender, role_id)
                os.popen(shell)
            except:
                break


if __name__ == "__main__":
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect to server 20
    # s.connect(('128.14.230.246', 30000))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        init_connection(),
        read_packages(),
        send_heart_beat(),
        send_routin()
    ))
    loop.close()


