#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import logging

from aiohttp import web

from lib import record_player, save_names, is_target, get_player_info


routes = web.RouteTableDef()
logging.basicConfig(level=logging.INFO)


check_pool = dict()

bomb_pool = list()

@routes.get('/online')
async def online(request):
    global check_pool
    global bomb_pool
    query = request.query
    name = query["name"]
    level = int(query["level"])
    gender = query["gender"]
    role_id = int(query["role_id"])
    player = (name, level, gender, role_id)
    if level > 20:
        record_player([player])
        key = (int(time.time()))
        threshold = 6
        if key in check_pool:
            check_pool[key].append(player)
            if len(check_pool[key]) >= threshold:
                logging.info("xx players:", check_pool[key])
                save_names(check_pool[key])
            if not key in check_pool:
                check_pool = {key: [player]}
        if role_id not in bomb_pool and is_target(role_id):
            logging.info("start bomb: {}".format(str(player)))
            os.popen("pipenv run python bomb.py {} 1200 1>>bomb.log 2>>bomb.log &".format(role_id))
            bomb_pool.append(role_id)
    return web.Response(text="ok")

@routes.get('/offline')
async def offline(request):
    role_id = request.query["role_id"]
    player = get_player_info(role_id)
    logging.info("{} is offline".format(str(player)))
    bomb_pool.remove(role_id)
    return web.Response(text="ok")


app = web.Application()
app.add_routes(routes)
web.run_app(app, port=7788)