#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sqlite3
import sys

names = sys.argv[1:]

conn = sqlite3.connect("data.db")
conn.isolation_level = None
c = conn.cursor()

c.execute("SELECT role_id FROM all_players WHERE name in (%s)" % ",".join("'%s'"%n for n in names))

ids = []
for row in c.fetchall():
    ids.append(str(row[0]))

print(",".join(ids))
