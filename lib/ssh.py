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
# Copyright: 2019 IBM
# Author: Abdul Haleem <abdhalee@linux.vnet.ibm.com>

import os
import sys
import time
import pexpect
from pexpect import pxssh


class ssh:

    '''
    This class contains the modules to perform various operations on an LPAR via ssh
    The Host IP, username and password of host have to be passed to the class intially
    while creating the object for the class.
    '''

    def __init__(self, ip, username, password):
        self.host_ip = ip
        self.user_name = username
        self.password = password

    def login(self):
        '''
        log in to lpar ssh
        '''
        if os.system('ping -c 2 ' + self.host_ip):
            logging.error('Unable to ping remote test system!')
            sys.exit(1)
        else:
            try:
                self.ssh = pxssh.pxssh()
                self.ssh.login(
                    self.host_ip, self.user_name, self.password, login_timeout=60)
                return self.ssh
            except pxssh.ExceptionPxssh, e:
                print "unable to ssh", str(e)
                sys.exit(1)

    def run_cmd(self, command, console, timeout=3000):
        try:
            console.sendline(command)
            console.prompt(timeout=timeout)
            time.sleep(0.5)
            res = console.before
            print res
            console.sendline("echo $?")
            console.prompt(timeout=3000)
            time.sleep(0.5)
            self.check = console.before
            if("0" in self.check):
                return res
            else:
                print "Command not executed successfully"
        except Exception, info:
            print info
            sys.exit(1)
