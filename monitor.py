#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random
import socket
import time
import sys
import os
import  asyncio

from lib import user_do, login_verify, decode_readable_string, find_names, decode_players, save_names, record_player, is_target

version = '1.5.60090'
imei = "".join(str(random.randint(0,9)) for x in range(1, len("863272039030961")+1))
email = sys.argv[1]
user_id, token = user_do(email, imei)
session = login_verify(user_id, token, version)


def make_logon_data():
    package_data = b'\x09'
    package_data += bytes(version, 'utf8')
    package_data += b'\x14\x00\x04\x00\x07'
    package_data += b'a8_card'
    package_data += b'\x00\x20'
    package_data += bytes(user_id, 'utf8')
    package_data += b'\x0f'
    package_data += bytes(imei+';Android OS 9.0.1 / API-28 (V417IR/eng.root.20181010.162559)', 'utf8')
    package_data += b'\x0c'
    package_data += b'HuaweiMate20@'
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
            if head == b'\x00\x00\x00\x07\x01\x00\x1b':
                role_id = int.from_bytes(body[-4:], byteorder="little")
                print(role_id, "offline")
                shl = 'curl "localhost:7788/offline?role_id={}" 1>>/dev/null 2>>/dev/null &'.format(role_id)
                os.popen(shl)
            continue
        # print("head:", head)
        # if int.from_bytes(head, byteorder='big') < 640000:
            # print("body:", body)
        readable_string = decode_readable_string(body)
        # print(readable_string)
        # names = find_names(readable_string)
        names = decode_players(body)
        if names:
            for n in names:
                name, level, gender, role_id = n
                if level >= 25:
                    print(n)
                    shell = 'curl "localhost:7788/online?name={}&level={}&gender={}&role_id={}" 1>>/dev/null 2>>/dev/null &'.format(name, level, gender, role_id)
                    os.popen(shell)
        #    if len(name) in (2, 3) or (len(name) == 4 and name.isdigit()):  # system default names are 2 or 3 length
        #        now = time.time()
        #        if now - pool_time >= 1:
        #            # refresh pool
        #            pool_time = now
        #            bn_pool = set(names)
        #        else:
        #            bn_pool.add(names[0])
        #if len(bn_pool) >= 6:
        #    print("=======================================================")
        #    print("|          SB FOUND !!!!!!!!!!!                       |")
        #    print("=======================================================")
        #    print(len(bn_pool), bn_pool)
        #    save_names(list(bn_pool))


reader, writer = None, None

async def init_connection():
    global reader
    global writer
    reader, writer = await asyncio.open_connection('128.14.230.246', 30000)
    writer.write(make_logon_data())


if __name__ == "__main__":
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect to server 20
    # s.connect(('128.14.230.246', 30000))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        init_connection(),
        read_packages(),
        send_heart_beat(),
    ))
    loop.close()


