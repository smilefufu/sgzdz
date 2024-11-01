#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
from functools import reduce
import traceback
from hammer import do

server_id = 0


def worker(buyer, smasher):
    assert server_id != 0, "wrong server_id!"
    buyer = buyer.strip()
    smasher = smasher.strip()
    print("buyer", buyer, "smasher", smasher)
    try:
        buyer_gold, smasher_gold = do(buyer, smasher, server_id)
        print(buyer_gold, smasher_gold)
        assert smasher_gold >= 41180, "unexcepted error! {} {}".format(buyer, smasher)
        print("==============={}:{}======{}:{}==============".format(buyer, buyer_gold, smasher, smasher_gold))
        return smasher
    except AssertionError:
        print("smasher_gold not enough")
        exit()
    except:
        print(traceback.format_exc())
        print("==============something wrong=====================")
        return buyer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("account_file", help="账号文件，第一行有本金")
    parser.add_argument("server_id", help="login server id", type=int)
    args = parser.parse_args()
    account_file = args.account_file
    server_id = args.server_id
    f = open(account_file)
    reduce(worker, f.readlines())
