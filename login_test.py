#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random
import socket
import time
import sys
import os
import  asyncio

from lib import user_do, login_verify, decode_readable_string, find_names, decode_players, save_names, record_player, is_target, body_test

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
    package_data += bytes(imei+';Android OS 6.0.1 / API-23 (V417IR/eng.root.20180122.162559)', 'utf8')
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

        print("head:", head)
        print("body:", body)
        readable_string = decode_readable_string(body)
        print(readable_string)
        print(body_test(body))





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


