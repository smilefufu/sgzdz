#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import time
import math
import argparse
from hammer import SGZDZ

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("collector", help="gold collector email")
    parser.add_argument("prefix", help="pig smasher email list")
    parser.add_argument("range", help="pig smasher email list")
    parser.add_argument("server_id", help="login server id", type=int)
    args = parser.parse_args()
    collector_email = args.collector
    prefix = args.prefix
    sp = args.range.split("-")
    assert len(sp[0]) == len(sp[1])
    pad = len(sp[0])
    server_id = args.server_id
    collector = SGZDZ(collector_email, server_id)
    if sp[0] != '':
        rng = range(*[int(x) for x in sp])
        tmp = "{}{:0>"+str(pad)+"}@gmail.com"
        email_list = [tmp.format(prefix, i) for i in rng]
    else:
        conn = sqlite3.connect("data.db")
        conn.isolation_level = None   # auto commit
        c = conn.cursor()
        table_name = 'pigs_{}'.format(server_id)
        c.execute("SELECT email FROM " + table_name + " WHERE email like ? and level >=20 and gold between 100 and 20000", ("%"+prefix+"%", ))
        email_list = [row[0] for row in c.fetchall()]
    for email in email_list:
        if email == collector_email:
            continue
        try:
            smasher = SGZDZ(email, server_id)
            print("collecting email:", email, "with gold:", smasher._gold)
            if smasher._gold > 39000 or smasher._gold < 100:
                # TODO
                print("do next target....")
                smasher.close()
                continue
            if not [card_name for card_name, card_id, cd in collector._purple_cards if cd == 0]:
                print("no purple card!!!")
                exit()
            for card_name, card_id, cd in collector._purple_cards:
                if cd == 0:
                    print("using", card_name, card_id, "to collect", smasher._gold, end='')
                    collector.ensure_connection()
                    price = collector.query_price(card_id)
                    if not price:
                        collector.ensure_connection()
                        continue
                    base_price = int(price/2)
                    max_price = price * 10
                    step = int(price/10)
                    if max_price <= smasher._gold:
                        sell_price = max_price
                    else:
                        times = math.floor((smasher._gold - base_price)/step)
                        sell_price = base_price + step * times
                    print("at price:", sell_price)
                    market_id = collector.put_market(card_id, sell_price)
                    # time.sleep(1)
                    smasher.buy(market_id)
                    # time.sleep(1)
                    collector.harvest(market_id)
                    print("collector:", collector._gold, "smasher", smasher._email, smasher._gold)
                    print("collector purple cards:", len(collector._purple_cards))
                    smasher.close()
                    break
        except:
            import traceback
            print(traceback.format_exc())
            exit()
        collector.ensure_connection()
