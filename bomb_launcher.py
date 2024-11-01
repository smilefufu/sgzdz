#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
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


@routes.get('/detail')
async def status(request):
    if bomb_pool:
        conn = sqlite3.connect("data.db")
        conn.isolation_level = None   # auto commit
        c = conn.cursor()
        c.execute("SELECT role_id, name, level, atk FROM sbs WHERE role_id in ({})".format(",".join(str(k) for k in bomb_pool.keys())))
        players = ["{}, {}, {}级，战力{}".format(*i) for i in c.fetchall()]
    else:
        players = []
    return web.Response(text="\n".join(players))

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
        t = bomb_pool[role_id]
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

@routes.get('/attack')
async def attack(request):
    is_on = os.popen("ps aux | grep new_bomb.py | grep -v grep").read()
    if is_on:
        html = "<h1>attack is on</h1>"
    else:
        html = """
        <h1>
        <a href='/bomb'>bomb!</a>
        </h1>
        """
    return web.Response(body=html, headers={'Content-Type': "text/html; charset=utf-8"})

@routes.get('/bomb')
async def bomb(request):
    ref = request.headers.getall('Referer', [])
    host = request.headers.getall('Host', [])
    if ref and host[0] in ref[0]:
        # from my page
        is_on = os.popen("ps aux | grep new_bomb.py | grep -v grep").read()
        if not is_on:
            # not on yet
            os.system("pipenv run python new_bomb.py 1>bomb_auto.log 2>bomb_auto.log &")
            raise web.HTTPFound('/attack')
        else:
            return web.Response(text="attack is on")
    else:
        return web.Response(text="unauthorized access!")


app = web.Application()
app.add_routes(routes)
web.run_app(app, port=7788)
