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
# Author: Harish <harish@linux.vnet.ibm.com>
#         Abdul Haleem <abdhalee@linux.vnet.ibm.com>

import time
import sys
import re
import logging
import pexpect


class ipmi:

    def __init__(self, host_name, user_name, password):
        self.host_name = host_name
        if user_name == '':
            self.user_name = ''
        else:
            self.user_name = " -U %s " % user_name
        self.password = password

    def run_cmd(self, cmd, console, timeout=300):
        time.sleep(2)
        console.sendline(cmd)
        time.sleep(5)
        try:
            rc = console.expect(
                [r"\[pexpect\]#$", pexpect.TIMEOUT], timeout)
            if rc == 0:
                res = console.before
                res = res.splitlines()
                return res
            else:
                res = console.before
                res = res.split(cmd)
                return res[-1].splitlines()
        except pexpect.ExceptionPexpect, e:
            console.sendcontrol("c")
            print "IPMI Command execution failed"
            print str(e)
            sys.exit(1)

    def bso_auth(self, console, username, password):
        time.sleep(2)
        console.sendline('telnet github.com')
        time.sleep(5)
        try:
            rc = console.expect(["Username:", "refused", "login:"], timeout=60)
            if rc == 0:
                console.sendline(username)
                rc1 = console.expect(
                    [r"[Pp]assword:", pexpect.TIMEOUT], timeout=120)
                time.sleep(5)
                if rc1 == 0:
                    console.sendline(password)
                    rc2 = console.expect(
                        ["uccess", pexpect.TIMEOUT], timeout=120)
                    if rc2 == 0:
                        print "BSO is passed"
                    else:
                        print "BSO authentication has failed"
                        sys.exit(1)
                else:
                    sys.exit(1)
            elif rc == 1 or rc == 2:
                print "BSO is already passed"
                return
            else:
                print "Problem passing BSO"
                sys.exit(1)
        except pexpect.ExceptionPexpect, e:
            print "IPMI Command execution failed"
            print str(e)
            sys.exit(1)

    def check_kernel_panic(self, console):
        list = [
            "Kernel panic", "Aieee", "soft lockup", "not syncing", "Oops", "Bad trap at PC",
            "Unable to handle kernel NULL pointer", "Unable to mount root device", "grub>", "grub rescue", "\(initramfs\)", pexpect.TIMEOUT]
        try:
            rc = console.expect(list, timeout=120)
            if rc in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                print "system got " + list[rc] + ", exiting"
                return "panic"
            else:
                pass
        except:
            pass

    def run_build(self, cmd, console):
        time.sleep(2)
        console.sendline(cmd)
        time.sleep(5)
        try:
            rc = console.expect(
                ["Kernel Building Complete", "TEST: installing and booting the kernel", "Report successfully", pexpect.TIMEOUT], timeout=7200)
            if rc == 0:
                return "build"
            elif rc == 1:
                res = console.before
                res = res.splitlines()
                return "kexec"
            elif rc == 2:
                return "report"
            else:
                pass
        except:
            print "Time Out exceeded"
            sys.exit(1)

    def run_login(self, console):
        time.sleep(2)
        while True:
            panic = self.check_kernel_panic(console)
            if panic == "panic":
                print "Exiting ..."
                sys.exit(1)
            try:
                rc = console.expect(
                    ["login:", "Report successfully", pexpect.TIMEOUT], timeout=300)
                if rc == 0:
                    res = console.before
                    res = res.splitlines()
                    return "Login"
                elif rc == 1:
                    return "Error"
                else:
                    pass
            except:
                pass

    def activate(self):
        print "running:ipmitool -I lanplus %s -P %s  -H %s sol activate" % (self.user_name, self.password, self.host_name)
        con = pexpect.spawn('ipmitool -I lanplus %s -P %s -H %s sol activate' %
                            (self.user_name, self.password, self.host_name), timeout=60)
        return con

    def deactivate(self):
        print "running:ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s sol deactivate" % (self.user_name, self.password, self.host_name)
        pexpect.run('ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s sol deactivate' %
                    (self.user_name, self.password, self.host_name), timeout=30)

    def chassisBios(self):
        print "running:ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis bootdev bios"
        pexpect.run('ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis bootdev bios' %
                    (self.user_name, self.password, self.host_name), timeout=30)

    def chassisOff(self):
        print "running:ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis power off" % (self.user_name, self.password, self.host_name)
        pexpect.run('ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis power off' %
                    (self.user_name, self.password, self.host_name), timeout=30)

    def chassisOn(self):
        print "running:ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis power on" % (self.user_name, self.password, self.host_name)
        pexpect.run('ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis power on' %
                    (self.user_name, self.password, self.host_name), timeout=30)

    def getconsole(self):
        self.deactivate()
        con = self.activate()
        time.sleep(5)
        print "Activating"
        time.sleep(5)
        con.logfile = sys.stdout
        con.delaybeforesend = 0.9
        if con.isalive():
            return con
        else:
            print "Problem in getting the console"
            sys.exit(1)

    def status(self):
        con = pexpect.spawn('ipmitool -I lanplus %s -P %s  -H %s chassis status' %
                            (self.user_name, self.password, self.host_name))
        while con.isalive():
            time.sleep(2)
        cmd = ''.join(con.readlines())
        if 'on' in cmd.split("\n")[0]:
            return True
        return False

    def set_unique_prompt(self, console, username, password):
        rc = console.expect_exact(
            "[SOL Session operational.  Use ~? for help]\r\n", timeout=300)
        if rc == 0:
            print "Got ipmi console"
        else:
            sys.exit(1)
        time.sleep(5)
        console.send("\r")
        time.sleep(3)
        try:
            rc = console.expect_exact(["login: "], timeout=60)
            if rc == 0:
                console.sendline(username)
                rc = console.expect(
                    [r"[Pp]assword:", pexpect.TIMEOUT], timeout=120)
                time.sleep(5)
                if rc == 0:
                    console.sendline(password)
                    rc = console.expect(
                        ["Last login", "incorrect"], timeout=60)
                    if rc == 1:
                        print "Wrong Credentials"
                        sys.exit(1)
                else:
                    sys.exit(1)
            else:
                console.expect(pexpect.TIMEOUT, timeout=30)
                print console.before
        except pexpect.ExceptionPexpect, e:
            console.sendcontrol("c")
            console.expect(pexpect.TIMEOUT, timeout=60)
            print console.before
        time.sleep(5)
        console.sendline("PS1=[pexpect]#")
        rc = console.expect_exact("[pexpect]#")
        if rc == 0:
            print "Shell prompt changed"
        else:
            sys.exit(1)

    def get_type(self, console):
        rc = console.expect_exact(
            "[SOL Session operational.  Use ~? for help]\r\n", timeout=300)
        if rc == 0:
            print "Got ipmi console : First run"
        else:
            sys.exit(1)
        time.sleep(5)
        console.send("\r")
        time.sleep(3)
        try:
            rc = console.expect(
                ["\[.+\#", "petitboot", "login:", "(initramfs)"], timeout=400)
            if rc == 0:
                rc_in = console.expect(["login:", pexpect.TIMEOUT], timeout=120)
                if rc_in == 0:
                    return "login"
                elif rc_in == 1:
                    return "logged"
            elif rc == 1:
                return "petitboot"
            elif rc == 2:
                return "login"
            elif rc == 3:
                return "initramfs"
        except pexpect.ExceptionPexpect, e:
            print "Console connect timedout: chasis reboot"
            console.send('~.')
            time.sleep(10)
            console.close()
            return "timeout"

    def login(self, console, username, password):
        console.sendline(username)
        rc = console.expect(
            [r"[Pp]assword:", pexpect.TIMEOUT], timeout=120)
        time.sleep(5)
        if rc == 0:
            console.sendline(password)
            rc_l = console.expect(
                ["Last login:", "incorrect", pexpect.TIMEOUT], timeout=300)
            if rc_l == 1:
                print "Error in logging.Wrong Credentials"
                sys.exit(1)
        else:
            sys.exit(1)

    def handle_reboot(self, disk, host_details):
        console = self.getconsole()
        console_type = self.get_type(console)

        if console_type == 'timeout':
            logging.info(
                "Do a chassis power of-on to get system to normal state")
            if self.status():
                self.chassisOff()
                while self.status():
                    logging.info("waiting for chassis OFF ...")
                    time.sleep(1)
                time.sleep(60)
                self.chassisOn()
                time.sleep(60)
                while not self.status():
                    logging.info("waiting for chassis ON ...")
                    time.sleep(1)
                if not self.status():
                    sys.exit(0)
            else:
                self.chassisOn()
                time.sleep(60)
                while not self.status():
                    logging.info("waiting for chassis ON ...")
                    time.sleep(1)
                if not self.status():
                    sys.exit(0)

            time.sleep(10)
            console = self.getconsole()
            time.sleep(15)
            console_type = self.get_type(console)
        if console_type == 'initramfs':
            logging.info("Initramfs Shell")
            console.sendline('reboot')
            rc = console.expect(["Exit to shell"], timeout=1500)
            if rc == 0:
                logging.info('Exiting Shell')
                console.sendline("\r")
                rc1 = console.expect(
                    ["Exiting petitboot", "login:"], timeout=200)
                if rc1 == 0:
                    logging.info("Continuing")
                if rc1 == 1:
                    logging.info("Logging-in after initramfs")
                    self.login(console, host_details[
                        'username'], host_details['password'])
            else:
                logging.info("Console did not reach Petitboot")
        elif console_type == 'login':
            logging.info("Logging into system")
            self.login(console, host_details[
                           'username'], host_details['password'])
        elif console_type == 'logged' or console_type == 'petitboot':
            # Find the partition of installation on top of the disk
            logging.info("System Logged in/Petitboot state")
        console.sendline("PS1=[pexpect]#")
        rc = console.expect_exact("[pexpect]#")
        if rc == 0:
            logging.info("Shell prompt changed")
        else:
            sys.exit(1)
        self.run_cmd('cd', console)
        self.run_cmd('cd', console)
        time.sleep(10)
        uuid_result = self.run_cmd(
            'blkid /dev/disk/by-id/' + disk + '\r', console)
        if uuid_result[1] == '[pexpect]#':
            logging.error(
                "Disk ID not found. OS may not be installed in disk")
            sys.exit(1)
        for uid in uuid_result:
            UUID_match = re.search('UUID=(.*)', uid)
            if UUID_match:
                break
        if not UUID_match:
            logging.error(
                "UUID cannot be found of the boot partition")
            sys.exit(1)
        UUID = UUID_match.group(1)
        UUID_list = re.findall('"([^"]*)"', UUID)
        logging.info('%s', UUID_list[0])
        console.sendline(
            'nvram --update-config petitboot,bootdev=uuid:' + str(UUID_list[0]))
        console.sendline('nvram --update-config auto-boot?=true\r')
        time.sleep(5)
        console.sendline('reboot')
        pet_result = console.expect(
            ['Petitboot', pexpect.TIMEOUT], timeout=3600)
        if pet_result == 1:
            logging.error("System took more than 1 hour.. Exiting")
            sys.exit(1)
        rc_reb = console.expect('login:', timeout=1500)
        if rc_reb == 0:
            logging.info("Reboot successful.")
        self.close_console(console)


    def close_console(self, console):
        console.send('~.')
        time.sleep(10)
        console.close()
