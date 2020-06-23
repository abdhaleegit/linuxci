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


cifile = '/home/jenkins/userContent/distro-ci/CIFile'
ci_tmpfile = '/home/jenkins/userContent/distro-ci/file.tmp'
jenkinsrun_file = '/home/jenkins/userContent/distro-ci/jenkinsrun_file'

# machine=sys.argv[1]

Testmachine = 'dummy'
testline = 0
result = False
arr = list()


def write_jenkinsfile(Testmachine):
    systemfile = open(jenkinsrun_file, 'a+')
    systemfile.write("%s\n" % Testmachine)
    systemfile.close()


def cifile_read(machine=''):
    global Testmachine
    global testline
    datafiles = open(cifile)
    for lines in datafiles:
        if testline:
            break
        if any(ext in lines for ext in machine):
            continue
        value = lines.split('\n')
        value = value[:-1]
        key = ['platform', 'Testmachine', 'build_trigger', 'DistroName',
               'Test', 'version', 'inputfile', 'kvmtest_input', 'link', 'issue']
        i = 0
        for val in value[0].split(','):
            print key[i]+'=' + val
            i = i+1
            if i == 2:
                Testmachine = val
                write_jenkinsfile(Testmachine)
            testline = 1


datafile = open(jenkinsrun_file)
num_lines = sum(1 for line in datafile)
datafile.close()
datafile = open(jenkinsrun_file)

for line in datafile:
    value = line.split('\n')
    machine = value[0]
    if num_lines >= 2 and not machine == 'start':
        arr.append(machine)
    if num_lines == 1:
        arr.append(machine)

datafile.close()


cifile_read(arr)

f = open(cifile, 'r')
fw = open(ci_tmpfile, 'w')

lc = 0
for line in f:
    if lc == 0 and Testmachine in line:
        lc = 1
    else:
        fw.write(line)
f.close()
fw.close()

os.rename(ci_tmpfile, cifile)
