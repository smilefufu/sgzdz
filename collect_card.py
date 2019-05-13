#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sqlite3
import argparse
from hammer import SGZDZ

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("collector", help="gold collector email")
    parser.add_argument("card_name", help="card_name to collect")
    parser.add_argument("count", help="count to collect")
    parser.add_argument("server_id", help="login server id", type=int)
    args = parser.parse_args()
    collector_email = args.collector
    count = int(args.count)
    server_id = args.server_id
    # collector = SGZDZ(None, server_id, token="bdf5047b3d1b4864aac24af1230df3c8", user_id="44cf30b8-abae-41d5-bcbc-f3e22c2ef21d")
    collector = SGZDZ(collector_email, server_id)
    conn = sqlite3.connect("data.db")
    conn.isolation_level = None   # auto commit
    c = conn.cursor()
    table_name = 'pigs_{}'.format(server_id)
    c.execute("SELECT email FROM " + table_name + " WHERE email != ? and cards like ? ORDER BY RANDOM()", (collector_email, "%" + args.card_name + "%", ))
    accounts = c.fetchall()
    if not accounts:
        c.execute("SELECT email FROM " + table_name + " WHERE email != ? ORDER BY RANDOM()", (collector_email, ))
        accounts = c.fetchall()
    for item in accounts:
        email = item[0]
        smasher = SGZDZ(email, server_id)
        # at least 2 gold card need to be left
        card_will_left = [card_name for card_name, card_id, cd in smasher._gold_cards if card_name != args.card_name and cd == 0]
        if len(card_will_left) < 2:
            smasher.close()
            continue
        print("collecting from", email, ":", ",".join(card_name for card_name, card_id, cd in smasher._gold_cards + smasher._purple_cards))
        cards = smasher._purple_cards if args.card_name == "purple" else smasher._gold_cards + smasher._purple_cards
        for card_name, card_id, cd in cards:
            if cd == 0 and (card_name == args.card_name or args.card_name == "purple"):
                print("collecting:", card_name, card_id)
                price = smasher.query_price(card_id)
                base_price = int(price/2)
                if collector._gold < base_price:
                    print("NOT ENOUGH GOLD!!!")
                    exit()
                market_id = smasher.put_market(card_id, base_price)
                time.sleep(1)
                collector.buy(market_id)
                time.sleep(1)
                smasher.harvest(market_id)
                count -= 1
            if count == 0:
                smasher.close()
                collector.close()
                exit()
        smasher.close()
