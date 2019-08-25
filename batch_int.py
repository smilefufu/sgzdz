#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("template", help="string template like 'xxx{}@gmail.com'")
    parser.add_argument("padLength", help="0 pad length", type=int)
    parser.add_argument("startIndex", help="operate on which server", type=int)
    parser.add_argument("endIndex", help="param for op", type=int)
    args = parser.parse_args()
    assert "startIndex must less than endIndex!", args.startIndex < args.endIndex
    for idx in range(args.startIndex, args.endIndex+1):
        idx_tpl = '{:0>%s}' % args.padLength
        print(args.template.format(idx_tpl.format(idx)))
