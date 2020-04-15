# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 15:45:42 2020

@author: Chan Chak Tong
"""

import argparse
from worm import Worm
parser = argparse.ArgumentParser()
parser.add_argument('group', help='the group link on FACEBOOK')
parser.add_argument('keyword', help='the keyword for describing the product you want')
parser.add_argument('--top', default=10, type=int, help='Search top-K results')
parser.add_argument('--scroll_time', default=6, type=int, help='the times of scrolling the window')
parser.add_argument('--freq', default=30, type=int, help='the updating frequency')
args = parser.parse_args()

worm = Worm()
worm.start(args.group)
worm.listen(args.keyword, args.top, args.scroll_time, args.freq)