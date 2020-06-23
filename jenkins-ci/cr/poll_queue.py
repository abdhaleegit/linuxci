#!/usr/bin/python

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
# Copyright: 2020 IBM
# Author: Praveen K Pandey <praveen@linux.vnet.ibm.com>

import os
import sys

build_notifier_loc = '/home/jenkins/userContent/distro-ci/jenkinsrun_file'
num_lines = sum(1 for line in open(build_notifier_loc, 'r'))
cifile = '/home/jenkins/userContent/distro-ci/CIFile'

result = False
arr = list()
testline = 0


def cifile_read(machine=''):
    global testline
    datafiles = open(cifile)
    for lines in datafiles:
        if testline:
            break
        if any(ext in lines for ext in machine):
            continue
        else:
            sys.exit(0)


def check_value():
    datafile = open(build_notifier_loc, 'r')
    for line in datafile:
        value = line.split('\n')
        machine = value[0]
        if num_lines >= 2 and not machine == 'start':
            arr.append(machine)
        if num_lines == 1:
            arr.append(machine)
    datafile.close()


with open(build_notifier_loc, 'r') as file:
    if num_lines == 5:
        sys.exit(1)
check_value()
cifile_read(arr)
sys.exit(1)
