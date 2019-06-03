#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
from functools import reduce
import traceback
from hammer import SGZDZ


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("buyer_email", help="本金账号")
    parser.add_argument("prefix", help="系列前缀")
    parser.add_argument("id_range", help="系列范围")
    parser.add_argument("server_id", help="login server id", type=int)
    args = parser.parse_args()
    buyer_email = args.buyer_email
    prefix = args.prefix
    id_range = args.id_range
    server_id = args.server_id

    start, end = id_range.split("-")
    assert int(end) >= int(start)
    pad = len(end)
    start = int(start)
    end = int(end) + 1

    buyer = SGZDZ(buyer_email, server_id)
    for n in range(start, end):
        tpl = "{}{:0>"+str(pad)+"}@gmail.com"
        smash_email = tpl.format(prefix, n)
        smasher = SGZDZ(smash_email, server_id)
        if smasher._info["level"] < 30:
            print(smasher._info)
            print("not level 30 yet", smasher._email)
            continue
        print("================start punch===============")
        print("buyer:{} {}\tsmasher:{} {}".format(buyer._email, buyer._gold, smasher._email, smasher._gold))
        need_gold = 39121
        if smasher._gold > 0 and smasher._gold < 30000:
            need_gold = need_gold - smasher._gold
        trade_gold = int(need_gold / 0.95) + 1
        card_list = smasher.sell(trade_gold)
        total_price = sum(price_to_put for card_name, card_id, price_to_put, market_id in card_list)
        if total_price < trade_gold:
            print("{} DO NOT HAVE ENOUGH CARD TO TRADE!".format(smasher._email))
            continue
        assert total_price <= buyer._gold, "BUYER {} DO NOT HAVE ENOUGH GOLD!".format(buyer._email)
        for card in card_list:
            print("buying...", card)
            card_name, card_id, price_to_put, market_id = card
            buyer.buy(market_id)
            smasher.harvest(market_id)
        assert smasher._gold >= 39121, "UNEXCEPTED TRADE RESULT!!!!!! NOT ENOUGH GOLD TO SMASH!!! {}".format(smasher._email)
        smasher.smash()
        print("smasher gold:", smasher._gold, "buyer gold:", buyer._gold)
        buyer.close()
        buyer = smasher
        buyer.ensure_connection()
