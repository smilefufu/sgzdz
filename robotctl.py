#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
import time
import datetime
import argparse


def count_robot(server_id):
    cnt = os.popen("ps aux | grep levelup_robot.py | grep \" {}$\" | grep -v grep | wc -l".format(server_id)).read()
    return int(cnt)

def log(*args):
    print("[{}]:".format(datetime.datetime.now()), *args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("op", help="operator instructure")
    parser.add_argument("server_id", help="operate on which server", type=int)
    parser.add_argument("--email", help="param for op")  # 可选参数
    args = parser.parse_args()

    conn = sqlite3.connect("data.db", timeout=10)
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    table_name = 'pigs_{}'.format(args.server_id)

    MAX_ONLINE_COUNT = 15

    if args.op == "add":
        # sql connection
        sql = "INSERT INTO {} (email) VALUES (?)".format(table_name)
        c.execute(sql, (args.email, ))
    elif args.op == "levelup":
        while True:
            now = datetime.datetime.now()
            if now.weekday() == 3 and now.hour == 9: # maintance time
                print("EXIT FOR MAINTANCE!")
                exit()
            cnt = count_robot(args.server_id)
            log("now robot:", cnt)
            if cnt < MAX_ONLINE_COUNT - 4:
                sql = "SELECT email FROM {} WHERE (last_login is null or datetime(last_login) < datetime('now', '-360 minute', 'localtime')) and email not like 'adorable%' ORDER BY level ASC LIMIT {}".format(table_name, MAX_ONLINE_COUNT - cnt)
                sql = "SELECT email FROM {} WHERE (last_login is null or datetime(last_login) < datetime('now', '-360 minute', 'localtime')) ORDER BY level ASC LIMIT {}".format(table_name, MAX_ONLINE_COUNT - cnt)
                log(sql)
                try:
                    c.execute(sql)
                except:
                    print("sql error")
                    continue
                rows = c.fetchall()
                now = datetime.datetime.now()
                if not rows and now.hour in (0, 1, 2, 3, 4, 5, 6, 10, 12, 13, 15, 16, 18, 19, 21, 22):
                    sql = "SELECT email FROM {} WHERE email not like 'adorable%' ORDER BY last_login ASC, level ASC LIMIT {}".format(table_name, MAX_ONLINE_COUNT - cnt)
                    sql = "SELECT email FROM {} WHERE datetime(last_login) < datetime('now', '-10 minute', 'localtime') ORDER BY last_login ASC, level ASC LIMIT {}".format(table_name, MAX_ONLINE_COUNT - cnt)
                    log(sql)
                    try:
                        c.execute(sql)
                    except:
                        print("sql error")
                        continue
                    rows = c.fetchall()
                if not rows:
                    time.sleep(10)
                for row in rows:
                    email = row[0]
                    log("start levelup", email)
                    os.popen("python levelup_robot.py {} {} 1>>lvl.{}.log 2>>lvl.{}.log &".format(email, args.server_id, args.server_id, args.server_id))
            else:
                time.sleep(10)
