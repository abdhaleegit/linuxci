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
#
# Copyright: 2020 IBM
# Author: Praveen K Pandey <praveen@linux.vnet.ibm.com>


import sys


kvm_input = sys.argv[1]

kvminput_arr = kvm_input[1:][:-1].split(':')

input_count = len(kvminput_arr)

key = ['guest', 'disk_type', 'network_type', 'only_filter', 'remote_ip']

print "testtype=kvm"
i = 0
for value in kvminput_arr:
    print key[i]+'=' + value
    i = i+1
