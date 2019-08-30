#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import socket
import time
import json
import datetime
import argparse
import sqlite3
from functools import reduce

import requests

from lib import login_verify, create_role, make_data, get_formation, body_test, make_battle_data, init_data, gen_name, make_login_server_data, make_quick_battle_data
from const import EPISODES, SERVER_LIST, STACK_ABLES, GUILD_ID, version


if __name__ == "__main__":

    # sql connection
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    series = """zilong lovely liubei caocao sunquan
sunce sunjian dianwei xuchu
caoren caohong caoxiu caopi caozhi
caozhang caorui caozhen caofang caomao
caohuan caoshuang caochun caoang caochong
yalishanda hanniba kaisa napolun wudawei
aogusidu maozedong napuleon augustus"""
    for idx, server_id in enumerate([20]):
        for prefix in series.split():
            sql = "UPDATE pigs_" + str(server_id) + " SET email = ? WHERE email = ?"
            for i in range(0, 100):
                bad_email = "{}{}@gmail.com".format(prefix, i)
                email = "{}{:0>3}@gmail.com".format(prefix, i)
                print "inserting:", email
                c.execute(sql, (email, bad_email))
