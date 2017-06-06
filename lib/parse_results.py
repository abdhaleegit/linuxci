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

import argparse
import re
import os

SID = ''
FILE_PATH = ''
FOUND = []
PATH = '/home/jenkins/jobs'
REPORT = '/root/report/status.log'
TRACES = ["Kernel panic", "Aieee", "soft lockup",
          "not syncing", "Oops", "Bad trap at PC",
          "Unable to handle kernel NULL pointer",
          "Unable to mount root device", "grub>",
          "grub rescue", "\(initramfs\)", "unhandled signal",
          "WARNING: CPU:", "Call Trace:", "BUG: unable to handle kernel NULL",
          "detected stalls on CPUs/tasks:", "detected stall on CPU",
          "NMI backtrace for cpu", "NMI watchdog: BUG: soft lockup - CPU",
          "unhandled signal", "Machine Check Exception", "WARNING: at", "Not tainted"
          "Unhandled CmdError: Command <make -j", "error:", "Backtrace:",
          "double linked list corrupted", "metadata I/O error", "Metadata corruption detected"
          "Segmentation fault", "Oops: Kernel access of bad area"]


def parse(path, trace):
    global SID, FILE_PATH
    for dir_path, dirs, file_names in os.walk(path):
        for file_name in file_names:
            path = os.path.join(dir_path, file_name)
            for line in file(path):
                if 'sid=' in line:
                    SID = line.strip('\n')
                if trace in line:
                    FILE_PATH = path
                    line = re.sub(r'.*]', ']', line)
                    return line.strip('\n')[1:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store", dest="build", help="Specify the build number of this job\
                        Usage: --build 154")
    parser.add_argument("--project", action="store", dest="project", help="Specify the project of this build\
                        Usage: --project K-Bot")
    options = parser.parse_args()
    if options.build:
        BUILD_NUMBER = options.build
    if options.project:
        JOB_NAME = options.project
    job_logs = "%s/%s/builds/%s/" % (PATH, JOB_NAME, BUILD_NUMBER)
    parse_log = os.path.join(job_logs + 'parse.log')
    with open(parse_log, 'a') as fd, open(REPORT, 'a') as fin:
        fd.write("\n # Result Analysis: " + ' JOB_ID:' + BUILD_NUMBER + ' #\n')
        fd.write("\n")
        fin.write('\n # START  :BUILD NUMBER :' + BUILD_NUMBER + ' #\n')
        fin.write("\n")
        for trace in TRACES:
            if trace not in FOUND:
                line = parse(job_logs, trace)
                if line and line != '\r':
                    fd.write(line + '\n Found in :' + FILE_PATH + '\n')
                    fd.write('\n')
                    fin.write(line + '\n Found in :' + FILE_PATH + '\n')
                    fin.write('\n')
        fin.write(
            '# END ' + SID + ' : BUILD NUMBER : ' + BUILD_NUMBER + ' #\n')
        fin.write(
            '-------------------------------------------------------------\n')
        fd.write(' # end ' + SID + ' #\n')
        fd.close()
        fin.close()
if __name__ == "__main__":
    main()
