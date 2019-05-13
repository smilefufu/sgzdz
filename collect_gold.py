#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
    # collector = SGZDZ(None, server_id, token="aa7a3c0ed85e4ab79592415e1eef058a", user_id="44cf30b8-abae-41d5-bcbc-f3e22c2ef21d")
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
        c.execute("SELECT email FROM " + table_name + " WHERE email like ? and gold between 1000 and 5000", ("%"+prefix+"%", ))
        email_list = [row[0] for row in c.fetchall()]
    for email in email_list:
        smasher = SGZDZ(email, server_id)
        print("collecting email:", email, "with gold:", smasher._gold)
        if smasher._gold > 39000 or smasher._gold < 1000:
            # TODO
            smasher.close()
            print("do next target....")
            continue
        if not [card_name for card_name, card_id, cd in collector._purple_cards if cd == 0]:
            print("no purple card!!!")
            exit()
        for card_name, card_id, cd in collector._purple_cards:
            if cd == 0:
                print("using", card_name, card_id, "to collect", smasher._gold)
                price = collector.query_price(card_id)
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
                time.sleep(1)
                smasher.buy(market_id)
                time.sleep(1)
                collector.harvest(market_id)
                print("collector:", collector._gold, "smasher", smasher._email, smasher._gold)
                print("collector purple cards:", len(collector._purple_cards))
                smasher.close()
                break
        # if collector._info["role_id"] in (347101, ) and collector._gold > 400 and not all(cd>0 for card_name, card_id, cd in smasher._purple_cards):  # enough vip level to get purple first
        #     for card_name, card_id, cd in smasher._purple_cards:
        #         if cd == 0:
        #             print("trading:", card_name, card_id)
        #             price = smasher.query_price(card_id)
        #             market_id = smasher.put_market(card_id, int(price/2))
        #             time.sleep(1)
        #             collector.buy(market_id)
        #             time.sleep(1)
        #             smasher.harvest(market_id)
        #             break
