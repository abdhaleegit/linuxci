#!/usr/bin/env python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright: 2024 IBM
# Author : Tejas Manhas <Tejas.Manhas@ibm.com>
# Co-Author : Abdul Haleem <abdhalee@linux.vnet.ibm.com>
#Functionality to store last good commit history for bisection

import json
import sys
import os
import argparse
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from lib import common_lib as cb


def fetch(sid,type):
    rrjson={}
    rjson=cb.read_json(cb.base_path+sid+'/'+sid+'.json')
    att = str(type+'goodCommit')
    if att in rjson:
        if rjson[att]:
            rrjson[att]=rjson[att]
        else:
            rrjson[att] = 'cd'
            cb.append_diff_json(cb.base_path+sid+'/'+sid+'.json',rrjson)
    else :
        rrjson[att] = 'c664e16bb1ba1c8cf1d7ecf3df5fd83bbb8ac15a'
        cb.append_diff_json(cb.base_path+sid+'/'+sid+'.json',rrjson)
    return rrjson[att]


def push(sid, goodcommit,type):
    gjson={}
    gjson[type+'goodCommit'] = goodcommit
    cb.append_diff_json(cb.base_path+sid+'/'+sid+'.json',gjson)
    return "UPDATED"


def process(*args):
    arg1=args[0]
    sys.path.append(os.path.join(arg1))
    num = len(args)
    if num == 2:
        arg2=args[1]
        res = fetch(arg1,arg2)

    elif num ==3:
        arg2=args[1]
        arg3=args[2]
        res =push(arg1,arg2,arg3)
    else :
        raise ValueError("Arguments are not valid for good-commit")
    return res


if __name__ == "__main__":
    argsi = sys.argv[1:]
    result = process(*argsi)
    serialized_result = json.dumps(result)
    print(serialized_result)
