#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import logging

from aiohttp import web

from lib import record_player, save_names, is_target


routes = web.RouteTableDef()
logging.basicConfig(level=logging.INFO)

conn = sqlite3.connect("data.db")
conn.isolation_level = None

check_pool = dict()

@routes.get('/online')
async def online(request):
    query = request.query
    name = query["name"]
    level = query["level"]
    gender = query["gender"]
    role_id = int(query["role_id"])
    player = (name, level, gender, role_id)
    if level > 20:
        record_player(player)
        key = (int(time.time()))
        threshold = 6
        if key in check_pool:
            check_pool[key].append(player)
            if len(check_pool[key]) >= threshold:
                logging.info("xx players:", check_pool[key])
                save_names(check_pool[key])
            if not key in check_pool:
                check_pool = {key: [player]}
        if is_target(role_id):
            logging.info("start bomb:", player)
            os.popen("pipenv run python bomb.py {} 1200 &".format(role_id))
    return web.Response(text="ok")

@routes.get('/offline')
async def offline(request):
    return web.Response(text="ok")


app = web.Application()
app.add_routes(routes)
web.run_app(app)
