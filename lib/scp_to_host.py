#!/usr/bin python

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
# Author: Harish <harish@linux.vnet.ibm.com>

import os
import sys
import pexpect
import argparse
sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from lib import common_lib as commonlib


def scp_id(sid, host_details):
    if os.path.exists(commonlib.base_path + sid + '/hostCopy.tar.gz'):
        print "Copying tar to host"
        commonlib.scp_to_host(
            commonlib.base_path + sid + '/hostCopy.tar.gz', host_details)
        os.system('rm -rf ' + commonlib.base_path + sid + '/hostCopy.tar.gz')
    sid_json = commonlib.read_json(
        commonlib.base_path + sid + '/' + sid + '.json')
    if sid_json['CONFIG'] == '' and sid_json['PATCH'] == '':
        print "NO FILES TO SCP"
        return
    else:
        if sid_json['CONFIG'] == '' or 'make' in sid_json['CONFIG']:
            config = ''
            print "NO CONFIG FILE"
        else:
            config = sid_json['CONFIG']
        if sid_json['PATCH'] == '':
            print "NO PATCH FILE"
        commonlib.scp_to_host(config + ' ' + sid_json['PATCH'], host_details)


def scp_manual(config, patch, host_details):
    manual_path = commonlib.get_output('pwd') + '/'
    if os.path.exists(manual_path + '/hostCopy.tar.gz'):
        print "Copying tar to host"
        commonlib.scp_to_host(manual_path + '/hostCopy.tar.gz', host_details)
        os.system('rm -rf ' + manual_path + '/hostCopy.tar.gz')

    if not os.path.exists(config) and not os.path.exists(patch):
        print "NO CONFIG FILE AND PATCH FILE"
        return
    else:
        if not os.path.exists(config) or 'make' in config:
            config = ''
            print "NO CONFIG FILE"
        if not os.path.exists(patch):
            patch = ''
            print "NO PATCH FILE"
        commonlib.scp_to_host(config + ' ' +
                              patch, host_details)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--id", action="store", dest="id", help="Specify the SID of the run\
                        Usage: --id sid")
    parser.add_argument("--host", action="store", dest="host", help="Specify the host details of the test\
                        Usage: --host hostname=hostname,username=username,password=password")
    parser.add_argument("--config", action="store", dest="config", help="Specify the name of config file user uploaded\
                        Usage: --config configfile-name")
    parser.add_argument("--patch", action="store", dest="patch", help="Specify the name of patch file user uploaded\
                        Usage: --id patchfile-name")

    options = parser.parse_args()
    host_details = commonlib.get_keyvalue(options.host)
    if options.id:
        scp_id(options.id, host_details)
    else:
        scp_manual(options.config, options.patch, host_details)
    print "SCP COMPLETE"

if __name__ == "__main__":
    main()
