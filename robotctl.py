#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
import time
import datetime
import argparse


def count_robot():
    cnt = os.popen("ps aux | grep levelup_robot.py | grep -v grep | wc -l").read()
    return int(cnt)

def log(*args):
    print("[{}]:".format(datetime.datetime.now()), *args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("op", help="operator instructure")
    parser.add_argument("server_id", help="operate on which server", type=int)
    parser.add_argument("--email", help="param for op")  # 可选参数
    args = parser.parse_args()

    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    table_name = 'pigs_{}'.format(args.server_id)

    MAX_ONLINE_COUNT = 10

    if args.op == "add":
        # sql connection
        sql = "INSERT INTO {} (email) VALUES (?)".format(table_name)
        c.execute(sql, (args.email, ))
    elif args.op == "levelup":
        while True:
            now = datetime.datetime.now()
            cnt = count_robot()
            if cnt == 0:
                sql = "SELECT email FROM {} WHERE last_login is null or datetime(last_login) < datetime('now', '-600 minute', 'localtime') ORDER BY level ASC LIMIT {}".format(table_name, MAX_ONLINE_COUNT)
                log(sql)
                c.execute(sql)
                rows = c.fetchall()
                if not rows:
                    time.sleep(60)
                for row in rows:
                    email = row[0]
                    log("start levelup", email)
                    os.popen("python levelup_robot.py {} {} 1>>lvl.log 2>>lvl.log &".format(email, args.server_id))
            else:
                time.sleep(10)
