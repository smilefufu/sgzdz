#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import random
import sqlite3
import datetime
import traceback

import requests

from const import CARD_CODE_PURPLE, CARD_CODE_GOLD, LAST_NAME, BOY_NAME, GIRL_NAME

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 8.0.0; en-us;) AppleWebKit/533.1 (KHTML, like Gecko) Version/5.0 Mobile Safari/533.1"
}

def baseN(num, b):
	return ((num == 0) and "0") or (baseN(num // b, b).lstrip("0") + "0123456789abcdefghijklmnopqrstuvwxyz"[num % b])

def decode_readable_string(data):
    # data is byte array
    ptr = 0
    ret = ""
    while ptr<len(data):
        c = data[ptr]
        if len(bin(c)) == 9: # 1 byte utf8
            ret += data[ptr:ptr+1].decode('utf8')
        elif len(bin(c)) == 10:
            if bin(c).startswith('0b110') and ptr+1<len(data) and len(bin(data[ptr+1])) == 10 and bin(data[ptr+1]).startswith('0b10'):
                try:
                    ret += data[ptr:ptr+2].decode('utf8')
                    ptr += 1
                except:
                    pass
            elif bin(c).startswith('0b1110') and ptr+2<len(data) and len(bin(data[ptr+1])) == len(bin(data[ptr+2])) == 10 and bin(data[ptr+1]).startswith('0b10') and bin(data[ptr+2]).startswith('0b10'):
                try:
                    ret += data[ptr:ptr+3].decode('utf8')
                    ptr += 2
                except:
                    pass
        elif c == 9:
            ret += '\t'
        ptr += 1
    return ret

def find_names(s):
    ret = []
    for name in re.findall('\t([^\t]\S*?)[woman|man]', s, re.M):
        if len(name) <= 6:
            ret.append(name)
    return ret

def decode_players(data):
    sp = re.split(b'w?o?man\x02.[\x04\x08].[\x05\x08]\x00[\s\S]\x00[\x00\x01]\x01\x00', data)
    if len(sp) < 2:
        # no player found
        return None
    player_data = sp[:-1]
    players = []
    for player in player_data:
        if player[-1] not in [3, 5]:
            continue
        gender = player[-1]
        level = player[-2]
        player = player[:-2]
        for i in range(2, len(player)):
            if player[-i] == i-1:
                # player[-i] is the name length byte
                try:
                    name = player[-i+1:].decode('utf8')
                    role_id = int.from_bytes(player[-i-13:-i-9], byteorder='little')
                    break
                except:
                    print('decode error!')
                    continue
        players.append((name, level, gender, role_id))
    return players


def user_do(username,imei, passwd='V0\/wJekk6Kk=', proxy=None):
    # return user_id and session for login_verify api
    version = 'Android1.0.1'
    tpl = '{"uid":"","token":"","uName":"%s","nickName":"","password":"%s","version":"%s","imei":"%s","authCode":"","flag":1,"isfast":"0","thirdType":1,"thirdToken":"","thirdUid":"","fbBusinessToken":"","language":"Cn","appKey":"76749c0621384a96b744ccb089567bcf"}'
    j = tpl % (username, passwd, version, imei)
    url = 'http://haiwaitest.3333.cn:8008/sdk/user/user.do'
    if proxy:
        proxies = dict(http=proxy, https=proxy)
        r = requests.post(url, headers=headers, data=j, proxies=proxies, timeout=5).json()
    else:
        r = requests.post(url, headers=headers, data=j).json()
    print(r)
    return r['uid'], r['token']

def login_verify(user_id, token, version='1.5.60090', proxy=None, server_id=20):
    # return tcp session
    url = 'http://sgz-login.fingerfunol.com:30006/entry_server/login_verify?version=%s&server_id=%s&userid=%s&channel=4&session=%s&platform=a8card&isdebug=False&activation_code=' % (version, server_id, user_id, token)
    if proxy:
        proxies = dict(http=proxy, https=proxy)
        r = requests.get(url, headers=headers, proxies=proxies, timeout=5).json()
    else:
        r = requests.get(url, headers=headers).json()
    print(r)
    return r['session']

def sqlite_init():
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS sbs (name varchar, level int, gender int, role_id int unique)")
    c.close()
    return conn

def save_names(names):
    conn = sqlite_init()
    c = conn.cursor()
    c.executemany("REPLACE INTO sbs VALUES (?, ?, ?, ?)", names)
    c.close()

def check_name(name):
    conn = sqlite_init()
    c = conn.cursor()
    c.execute("SELECT * FROM sbs WHERE name=?", name)
    result = c.fetchone()
    c.close()
    return bool(result)

def get_names():
    conn = sqlite_init()
    c = conn.cursor()
    c.execute("SELECT * FROM sbs")
    ret = c.fetchall()
    c.close()
    return ret

def get_player_info(role_id):
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None
    c = conn.cursor()
    c.execute("SELECT * FROM all_players WHERE role_id=?", (role_id, ))
    r = c.fetchone()
    c.close()
    return r
    pass

def record_player(players):
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS all_players (name varchar, level int, gender int, role_id int unique, login_time varchar)")
    data = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for player in players:
        name, level, gender, role_id = player
        data.append((name, level, gender, role_id, now))
    c.executemany("REPLACE INTO all_players VALUES (?, ?, ?, ?, ?)", data)
    c.close()
    conn.close()

def make_create_role_data(role_name, model):
    name = bytes(role_name, 'utf8')
    body = b'\x00\x01\x00\x00\x00\x00\x01'
    body += len(name).to_bytes(1, byteorder='big')
    body += name
    # role model: 01 m3, 02 w1, 03 m2, 04 w3, 05 m3, 06 w2
    body += model
    head = len(body).to_bytes(4, byteorder='big')
    return head+body

def create_role(s, role_name=None):
    """
    :s: the socket connection
    :returns: roleId, player_name
    """
    retry = 0
    name_pool = '幸段謝羊彬穆品狄琴芬丁墨鑫先耀嵇計岑昝樺熹忠賀才躍杜彪彭黃孟支良道房賓隗高博蔣吾石洋婁謙山婷龐談顏鋼慈明貝文超蔔尤愛紹伯全硯雅清昊翁楠袁戴壇元皓浩敏霖戎乾沙裘春柳雄應卞輝崗俊洪濱張苗雷龍顧凱魏危樊郎琰翰妍江中若葉繆吉合樂花祖何松傳邦糜慧迎梓邱執冉梁畢夏宣隆鵬思彰趙純止伶宋萬蘇洲竇莉涯毛坤鋒旭光竣巫璿曲義埃阮暉傑寧漩喻紫新晗雲非亞谷嫣範淦富雪午逸勝甄和童康也時辰鄒學翊翔卓之湛珂任川葛韶郝宇徐暴晨詹西琦宸董容濤燕伊啟烏磊許曆影陶勃宵蔡瑋皮米興貴費豪車健餘呂閃成弓枚薛晏芮芪汪常行季剛繼恬路祈單宝賁利錢荔彎群馮鄭強仇曉銳維熊瑞王凡訪伏殊紅疏世韋珺力捷戚胡紀河志諾生嵐賈蕭涔陳滑鈄駱蓬玉鐘馬劉項基珈與炎尹智靳境滕民朱稚筱昌靜衛伍向賽章解書諸姚仙陽唐姜秋豔子祁汲仰孔儲然盧久懿孫牧金田言培嶽多天煒舒霍羲大俞英奕君樹銘勇國曼軒鬱根刁卿潘酆湯郭虞錦臧禹偉建禮景盛嚴曹宮梅本龔茅倪籽峻羅莫宓壹森鳳威連廉奚安仲施藝鋮欒煜柏邢茂侯鄧淼傅褚雁席珮榮閔耶齊楊騰程絢惠林吳殷方泰竹海淵華堅裴呈希乙麻秦家遠班孜平符水祥粟焦聆鈞昕韓儀左藍振杭斌祝琅宏藤顯邴飛臻士昆夜'
    name_pool = list(name_pool)
    magic_pool = list('古月娜滾出二十區')
    models = [b'\x01', b'\x02', b'\x03', b'\x04', b'\x05', b'\x06']
    while retry < 10:  # atmost 10 times retry
        random.shuffle(name_pool)
        random.shuffle(models)
        random.shuffle(magic_pool)
        n = role_name or "".join(name_pool[:2]) + magic_pool[0] + "".join(name_pool[2:5])
        data = make_create_role_data(n, models[0])
        s.send(data)
        ret = s.recv(2048)
        retry += 1
        if ret[:4] == b'\x00\x00\x00\x06':
            print("name", n, "has been taken")
            continue
        else:
            try:
                role_id = int.from_bytes(ret[7:11], byteorder='little')
                role_name = ret[14:ret[13]+14].decode('utf8')
                return role_id, role_name
            except:
                print("decode return value error!")
                return None, None

def make_logon_data(version, user_id, imei, session):
    package_data = b'\x09'
    package_data += bytes(version, 'utf8')
    package_data += b'\x14\x00\x04\x00\x07'
    package_data += b'a8_card'
    package_data += b'\x00\x20'
    package_data += bytes(user_id, 'utf8')
    package_data += b'\x0f'
    package_data += bytes(imei+';Android OS 9.0.1 / API-28 (V417IR/eng.root.20190101.162559)', 'utf8')
    package_data += b'\x0c'
    package_data += b'HuaweiMate20@'
    package_data += b'\xac'
    package_data += bytes(session, 'utf8')
    logon_data = len(package_data).to_bytes(4, byteorder='big') + package_data
    return logon_data

def make_login_server_data(version, user_id, server_id, imei, session, os=None, phone=None):
    _os = bytes(os or 'Android OS 9.0.1 / API-28 (V417IR/eng)', 'utf8')
    _phone = bytes(phone or 'HuaweiMate21', 'utf8')
    _user_id = bytes(user_id, 'utf8')
    _imei = bytes(imei, 'utf8')
    _session = bytes(session, 'utf8')

    data = b'\x09'
    data += bytes(version, 'utf8')
    data += server_id.to_bytes(1, byteorder='big')
    data += b'\x00\x04'

    channel = bytes('a8_card', 'utf8')
    data += len(channel).to_bytes(2, byteorder='big')
    data += channel

    data += len(_user_id).to_bytes(2, byteorder='big')
    data += _user_id

    data += len(_imei).to_bytes(1, byteorder='big')
    data += _imei

    data += len(_os).to_bytes(1, byteorder='big')
    data += _os

    data += len(_phone).to_bytes(1, byteorder='big')
    data += _phone

    data += b'@'

    data += len(_session).to_bytes(1, byteorder='big')
    data += _session
    ret =  len(data).to_bytes(4, byteorder='big') + data
    print(ret)
    return ret


def validate_proxy(host, port):
    import socks
    import socket
    socks.set_default_proxy(socks.SOCKS5, host, port)
    try:
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(('128.14.230.246', 30000))
        s.close()
        r = requests.head("http://sgz-login.fingerfunol.com:30006", timeout=1)
        if r.status_code in [200, 404]:
            return True
    except:
        print(traceback.format_exc())
    return False

def add_proxy(proxies):
    # proxies is [(host, port), ...]
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS proxies (host varchar unique, port int)")
    c.executemany("REPLACE INTO proxies VALUES (?, ?)", proxies)
    c.close()
    conn.close()

def get_proxies(count=100):
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM proxies ORDER BY RANDOM() LIMIT ?", (count,))
        ret = c.fetchall()
        c.close()
        conn.close()
        return ret
    except:
        print(traceback.format_exc())
        return []


def del_proxy(host):
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None
    c = conn.cursor()
    c.execute("DELETE FROM proxies WHERE host=?", (host, ))
    c.close()
    conn.close()

def make_send_msg_data(msg, receiver_id, seq=3):
    body = seq.to_bytes(2, byteorder="big")
    body += b"\x00\x00\x00\x00\xdd\x00"
    msg_bytes = msg.encode("utf8")
    body += len(msg_bytes).to_bytes(2, byteorder="big") + msg_bytes + b'\x00'
    body += b"\x00\x00\x00\x00" + receiver_id.to_bytes(4, byteorder="little")
    body += b"\x00"
    return len(body).to_bytes(4, byteorder="big") + body

def make_bad_msg_data(msg, receiver_id, seq=3):
    body = seq.to_bytes(2, byteorder="big")
    body += b"\x00\x00\x00\x00\xdd\x00"
    msg_bytes = msg
    body += len(msg_bytes).to_bytes(2, byteorder="big") + msg_bytes + b'\x00'
    body += b"\x00\x00\x00\x00" + receiver_id.to_bytes(4, byteorder="little")
    body += b"\x00"
    return len(body).to_bytes(4, byteorder="big") + body

class Session():
    def __init__(self, email, passwd=None):
        self.conn = sqlite3.connect("data.db")
        self.conn.isolation_level = None
        c = self.conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS session (email varchar unique, user_id, token, session)")
        c.close()

    def get_session(self, email):
        c = self.conn.cursor()
        c.execute("SELECT user_id, token, session FROM session where email=?", (email, ))
        r = c.fetchone()
        c.close()
        return r

    def update_session(self, email, user_id, token, session):
        c = self.conn.cursor()
        c.execute("REPLACE INTO session VALUES (?, ?, ?, ?)", (email, user_id, token, session))
        c.close()

    def delete_session(self, email):
        c = self.conn.cursor()
        c.execute("delete from session WHERE email=?", (email, ))
        c.close()

def is_target(role_id):
    if role_id in range(348110, 348120):
        return True
    if role_id in [354974,354978,354976,354971,355105,354972,354977,354975,354979,354973]:
        # temp use
        return True
    if role_id == 347110:
        # guyuena
        return True
    if role_id == 348668:
        # yexin (@jinbi)
        return True
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None
    c = conn.cursor()
    c.execute("SELECT * FROM sbs WHERE role_id=?", (role_id, ))
    if c.fetchone():
        c.close()
        conn.close()
        return True
    c.execute("SELECT name FROM all_players where role_id=?", (role_id, ))
    r = c.fetchone()
    if r and r[0].isdigit() and int(r[0]) < 3000:
        c.close()
        conn.close()
        return True
    c.close()
    conn.close()
    return False

def body_test(body):
    # return: dict(action=action_type, args=somedict())
    if body.startswith(b"\x01\x007"): # guild info  \x01\x00\x37
        role_id = int.from_bytes(body[3:7], byteorder="little")
        name_length = body[9]
        name = body[10:10+name_length].decode('utf8')
        if body[33] == 0: # join guild ( maybe?)
            action = "guild join"
        elif body[36] == 1:
            action = "guild online"
        elif body[36] == 0:
            action = "guild offline"
        else:
            action = "guild unkown"
        return dict(action=action, args=dict(role_id=role_id, name=name))
    if body.startswith(b'\x01\x00\x28') or body.startswith(b'\x01\x00\x27'):
        # get a card
        card_id = body[3:11]
        card_code = body[11:15]
        return dict(action='get_card', args=dict(card=(card_code, card_id)))
    pass

def make_data(data_type):
    if data_type == "zumao":
        # 1. get zumao
        # 00 00 00 07 00 04 00 00 00 00 03
        return b"\x00\x00\x00\x07\x00\x04\x00\x00\x00\x00\x03"
    if data_type == "huangjin":
        # 2. chu zhan huangjin?
        # 00 00 00 07 00 05 00 00 00 00 06
        return b"\x00\x00\x00\x07\x00\x05\x00\x00\x00\x00\x06"
    if data_type == "yingzhaoruwu":
        # 3. ying zhao ru wu (2 packet)
        # 00 00 00 07 00 08 00 00 00 00 05 00 00 00 07 00 09 00 00 00 00 07
        return b"\x00\x00\x00\x07\x00\x08\x00\x00\x00\x00\x05\x00\x00\x00\x07\x00\x09\x00\x00\x00\x00\x07"

    if data_type == "tongmenxiangju":
        # 5. tongmenxiangju
        # 00 00 00 07 00 07 00 00 00 00 03
        pass
    if data_type == "first_battle_end":
        return b"\x00\x00\x00\x2f\x00\x05\x00\x00\x00\x00\x0a\x01\x00\x03\xae\x00\x01\x63\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


def make_story_data(index):
    battle_index = [2, 4, 10]
    return b"\x00\x00\x00\x07\x00\x04\x00\x00\x00\x00\x06" if index in battle_index else b"\x00\x00\x00\x07\x00\x04\x00\x00\x00\x00\x03"


def find_cards(data):
    cards = set()
    if b"sysMail_addressor_BlackWings" in data:
        end_pos = data.find(b"sysMail_addressor_BlackWings")
        search_data = data[:end_pos]
        # start  searching
        all_card_code = dict()
        all_card_code.update(CARD_CODE_GOLD)
        all_card_code.update(CARD_CODE_PURPLE)
        for card, code in all_card_code.items():
            idx = search_data.find(code)
            if idx > 8:
                card_id = search_data[idx-8:idx]
                cards.add((card, card_id))
    return cards


def init_data(data):
    # head is not included, only body
    # data[:12]  unknown
    # data[12:16] == data[16:20] role_id, repeat twice
    # data[20:22] == b'\x14\x00' fixed bytes
    # data[22] name length
    # data[23:23+data[22]] name
    # data[data[22]+23] model_id
    # data[data[22]+24] level
    # data[data[22]+25:data[22]+28] ==  b'\x00\xc8\x09'  unkown bytes
    # data[data[22]+35:data[22]+39] now exp
    # data[data[22]+28:data[22]+54] == b'\x00...  26 bytes 00
    # data[data[22]+54] == b'\x01'    data[data[22]+55] story_index
    ret = dict()
    ret['role_id'] = int.from_bytes(data[12:16], byteorder="little")
    name_length = data[22]
    if name_length:
        ret['name'] = data[23:23+name_length].decode('utf8')
    ret['model_id'] = data[name_length+23]
    ret['level'] = data[name_length+24]
    ret['exp'] = int.from_bytes(data[name_length+35:name_length+39], byteorder="little")
    unknow_strlen = data[name_length+52]
    ret['story_index'] = (data[name_length+unknow_strlen+54], data[name_length+unknow_strlen+55])
    ret['cards'] = find_cards(data[name_length+unknow_strlen+55:])
    return ret

def get_formation(cards, episode=None):
    formation = [b'\x00'*8] * 15
    if episode == '1-0':
        cardmap = dict(cards)
        formation[2] = cardmap['zumao']
        formation[8] = cardmap['xiaoqiao']
    else:
        for idx, card in enumerate(cards):
            if idx > 15:
                break
            formation[idx] = card[1]
    return b"".join(formation)


def make_battle_data(cards, episode):
    ep = list(map(int, episode.split("-")))
    help_episode = ['1-3']
    data = b'\x00\x00\x00\x85\x00\x04'
    data += b'\x00\x00\x00\x00\x09'
    data += ep[0].to_bytes(1, byteorder='big')
    data += ep[1].to_bytes(1, byteorder='big')
    data += b'\x00\x00\x0f'
    data += get_formation(cards, episode)
    data += b'\x00' if episode not in help_episode else b'\x01'
    return data


def make_quick_battle_data(chapter, section):
    # shao dang
    data = b'\x00\x00\x00\x09\x00\x04\x00\x00\x00\x00\x0b'
    data += chapter.to_bytes(1, byteorder='big')
    data += section.to_bytes(1, byteorder='big')
    return data


def gen_name(seed=None, gender=3):
    random.shuffle(LAST_NAME)
    last_name = LAST_NAME[0]
    FN = BOY_NAME if gender == 3 else GIRL_NAME
    random.shuffle(FN)
    first_name = FN[0]
    name = last_name + first_name
    if str(seed).isdigit():
        seed = int(str(seed)) % 10000
    if seed:
        sd = int.from_bytes(str(seed).encode('utf8'), byteorder="little")
        name += baseN(sd, 36)[:4]
    return name
