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
#
#

import os
import sys

ci_tmpfile = '/home/jenkins/userContent/distro-ci/jenkintmp.tmp'
ci_file = '/home/jenkins/userContent/distro-ci/jenkinsrun_file'

Testmachine = sys.argv[1]


f = open(ci_file, 'r')
fw = open(ci_tmpfile, 'w')

print Testmachine

lc = 0
for line in f:
    if Testmachine in line:
        lc = 1
        print Testmachine
    else:
        fw.write(line)
f.close()
fw.close()

os.system('cat %s ' % ci_tmpfile)
os.rename(ci_tmpfile, ci_file)
