#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

with open("20.txt", "r") as f:
    for line in f.readlines():
        email = line.split("@")[0].strip() + "@gmail.com"
        print("running:", email)
        os.system("python quick_levelup.py "+email+" 20")
