#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import logging
import json
import traceback

from aiohttp import web

from lib import record_player, save_names, is_target, get_player_info


routes = web.RouteTableDef()
logging.basicConfig(format='[%(asctime)s]: %(message)s', filename='launcher.log', level=logging.INFO)


all_ws = list()
bomb_pool = dict()

@routes.get('/status')
async def status(request):
    return web.Response(text=json.dumps(bomb_pool))


@routes.get('/target_online')
async def online(request):
    query = request.query
    role_id_list = [int(x) for x in query["role_id"].split(",")]
    for role_id in role_id_list:
        bomb_pool[role_id] = int(time.time())
    for ws in all_ws:
        await ws.send_str(json.dumps(bomb_pool))
    logging.info("{} online, now pool: {}".format(role_id, bomb_pool))
    return web.Response(text="ok")


@routes.get('/target_offline')
async def offline(request):
    role_id = int(request.query["role_id"])
    try:
        del bomb_pool[role_id]
        for ws in all_ws:
            await ws.send_str(json.dumps(bomb_pool))
        logging.info("{} offline, now pool: {}".format(role_id, bomb_pool))
    except:
        print(traceback.format_exc())
        pass
    return web.Response(text="ok")

@routes.get('/ws')
async def websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    all_ws.append(ws)
    print("in comming ws:", ws)
    await ws.send_str(json.dumps(bomb_pool))
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
                break
            else:
                await ws.send_str(json.dumps(bomb_pool))
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    all_ws.remove(ws)
    print('websocket connection closed')

    return ws


app = web.Application()
app.add_routes(routes)
web.run_app(app, port=7788)
