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
# Copyright: 2017 IBM
# Author: Abdul Haleem <abdhalee@linux.vnet.ibm.com>

import os
import json
import logging
import fcntl
import sys
import time
import errno
sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from lib import common_lib as commonlib


def check_machineQ(machine):
    machines = []
    while True:
        try:
            x = open(commonlib.machineQfile, 'r')
            fcntl.flock(x, fcntl.LOCK_EX | fcntl.LOCK_NB)
            machines = x.readlines()
            fcntl.flock(x, fcntl.LOCK_UN)
            x.close()
            for mlist in machines:
                if machine in mlist.split('\n'):
                    return True
            return False
        except IOError as ex:
            if ex.errno != errno.EAGAIN:
                raise
        else:
            time.sleep(0.1)


def pop_sid(SID):
    lines = []
    while True:
        try:
            with open(commonlib.schedQfile) as o:
                lines = o.readlines()
                o.close()
            with open(commonlib.schedQfile, 'w') as n:
                fcntl.flock(n, fcntl.LOCK_EX | fcntl.LOCK_NB)
                for item in lines:
                    if SID + '-' not in item.strip('\n'):
                        n.write(item)
                fcntl.flock(n, fcntl.LOCK_UN)
                n.close()
            if SID + '-' not in open(commonlib.schedQfile).read():
                return True
            return False
        except IOError as ex:
            if ex.errno != errno.EAGAIN:
                raise
        else:
            time.sleep(0.1)


def main():
    SID = ''
    jobs = []
    json_data = {}
    keyvals = {}
    if not os.path.exists(commonlib.machineQfile):
        open(commonlib.machineQfile, 'w').close()
    # Read top SID from the schedQfile
    if os.stat(commonlib.schedQfile).st_size != 0:
        with open(commonlib.schedQfile, 'r') as Q:
            jobs = Q.readlines()
            Q.close()
            for job in jobs:
                SID = job.replace('\n', '')
                SID = SID.split('-')[0]
                sidfile = commonlib.base_path + SID + '/' + SID + '.json'
                # get me the machine for the SID job
                if os.path.exists(sidfile):
                    json_data = commonlib.read_json(sidfile)
                    machine = json_data['BUILDMACHINE']
                    # Check the machine already in MQo
                    if not check_machineQ(machine):
                        commonlib.add_machineQ(machine)
                        if pop_sid(SID):
                            print("SID=" + SID)
                            if 'INPUTFILE' not in json_data:
                                json_data['INPUTFILE'] = 'None'
                            keyvals = {'kernel_git_repo': json_data['URL'], 'kernel_git_repo_branch': json_data['BRANCH'], 'inputfile': json_data['INPUTFILE'], 'configfile': json_data['CONFIG'], 'patchfile': json_data[
                                'PATCH'], 'tests': json_data['TESTS'], 'avtest': json_data['AVTEST'], 'buildmachine': json_data['BUILDMACHINE'], 'bootdisk': json_data['BOOTDISK']}
                            for key, val in keyvals.items():
                                print (key + "=" + str(val))
                            break

if __name__ == "__main__":
    main()
