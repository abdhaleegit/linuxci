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
import os


jenkinsrun_file = '/home/jenkins/userContent/distro-ci/jenkinsrun_file'
nsrun_file = '/home/jenkins/userContent/distro-ci/jenkinsruntmp'

Testmachine = ''


systemfile = open(jenkinsrun_file, 'a+')
systemfile.write("%s\n" % Testmachine)
systemfile.close()

f = open(jenkinsrun_file, 'r')
fw = open(nsrun_file, 'w')

lc = 0
for line in f:
    if lc == 0 and Testmachine in line:
        lc = 1
    else:
        fw.write(line)
f.close()
fw.close()

os.rename(nsrun_file, jenkinsrun_file)
