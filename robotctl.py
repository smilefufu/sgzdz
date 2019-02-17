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

    if args.op == "add":
        # sql connection
        sql = "INSERT INTO {} (email) VALUES (?)".format(table_name)
        c.execute(sql, (args.email, ))
    elif args.op == "levelup":
        while True:
            now = datetime.datetime.now()
            cnt = count_robot()
            if cnt < 10:
                # add to 10
                sql = "SELECT email FROM {} WHERE last_login is null or datetime(last_login) < datetime('now', '-700 min', 'localtime') ORDER BY level ASC LIMIT {}".format(table_name, 10-cnt)
                c.execute(sql)
                for row in c.fetchall():
                    email = row[0]
                    os.popen("pipenv run python levelup_robot.py {} {} &".format(email, args.server_id))
            elif now.hour == 3:
                # do attend, do daily
                pass
            else:
                time.sleep(10)
