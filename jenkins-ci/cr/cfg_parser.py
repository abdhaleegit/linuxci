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
# Author: Harish <harish@linux.vnet.ibm.com>


import ConfigParser
import argparse


def main():
    args = argparse.ArgumentParser()
    args.add_argument("-d", "--distro", help="echo the string for distro",
                      action="store", dest="distro", required=True)
    args = args.parse_args()
    config = ConfigParser.ConfigParser()
    config.read('/home/jenkins/userContent/distro-ci/distro_support.cfg')
    if args.distro:
        if args.distro in config.sections():
            build = config.get(args.distro, 'build')
            os = config.get(args.distro, 'os')
            test = config.get(args.distro, 'test')
            update = config.get(args.distro, 'update')
            link = config.get(args.distro, 'link')
            machines = config.get(args.distro, 'machine')
            inputfile = config.get(args.distro, 'inputfile')
            kvmtest_input = config.get(args.distro, 'kvmtest_input')
            for machine in machines.split(','):
                m_type = machine.split('_')
                platform = 'Power%s' % m_type[-1]
                systemfile = open(
                    "/home/jenkins/userContent/distro-ci/CIFile", "a+")
                systemfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
                    platform, m_type[0], build, os, test, update, inputfile, kvmtest_input, link))
                systemfile.close()
        else:
            print "Provide a valid input from ",  config.sections()
    else:
        print "Distro is required to run"


if __name__ == "__main__":
    main()
