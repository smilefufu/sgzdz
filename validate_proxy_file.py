#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib import validate_proxy, add_proxy

with open("sockslist", "r") as f:
    tmp = []
    for row in f.readlines():
        host, port = row.strip().split(":")
        print("validate:", host, port, end="....")
        if validate_proxy(host, int(port)):
            print("success!")
            tmp.append((host, int(port)))
            if len(tmp) > 100:
                add_proxy(tmp)
                tmp = []
    if tmp:
        add_proxy(tmp)
