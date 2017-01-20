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

import os
import time
import sys
import argparse
import re
import datetime
import logging
import pexpect
from lib import ipmi
from lib import hmc
from lib import bso_authenticator
from lib import common_lib as commonlib
from lib import scp_to_host as scplib

file_path = os.path.dirname(__file__)


def tear_down(obj, console):
    '''
    Clean host
    TODO: clear following
    1. hostCopy.tar.gz
    2. autotest
    3. avocado-fvt-wrapper
    4. patches
    '''
    logging.info('Cleaning Host')
    clean_list = ['hostCopy.tar.gz', commonlib.repo, 'avocado-fvt-wrapper',
                  'avocado-korg', 'autotest_results.tar.gz', 'avocado_results.tar.gz']
    if commonlib.repo == 'autotest':
        clean_list.extend(['autotest-client-tests.patch', 'autotest.patch'])
    for folder in clean_list:
        logging.info('Removing ' + folder)
        obj.run_cmd('rm -rf /root/' + folder, console)


def tar_in_host(obj, console, tag='autotest', path=commonlib.autotest_result):
    '''
    Tar the results in host
    '''
    logging.info('Tarring results in Host')
    obj.run_cmd('cd %s' % path, console)
    obj.run_cmd('tar -czf /root/%s_result.tar.gz %s --exclude=\'core\'' %
                (tag, '*'), console, timeout=3600)
    obj.run_cmd('cd ', console)


def check_ls(obj, console, val):
    '''
    Checks if dirctory is created with ls
    '''
    flag = False
    contents = obj.run_cmd('ls', console)
    for line in contents:
        for folder in line.split():
            if folder == val or val in folder:
                flag = True
                break
    return flag


def handle_console(obj, console, host_details, git, tests, bso_details, sid, avtest, hmc_flag=False):
    obj.run_cmd(' uname -r', console)
    obj.run_cmd('cd', console)
    result_dir, avocado_dir = run_function(
        obj, console, host_details, git, tests, bso_details, sid, avtest, hmc_flag)
    if result_dir:
        dest_dir = None
        result_path = os.path.join(file_path, 'results')
        if not os.path.exists(result_path):
            os.makedirs(result_path)
            dest_dir = os.path.join(
                result_path, 'kernelOrg_' + datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            os.makedirs(dest_dir)
            # Copying autotest results
            tar_in_host(obj, console)
            scp_from_host(
                host_details, dest_dir, files='autotest_result.tar.gz')
            commonlib.untar(
                os.path.join(dest_dir, 'autotest_result.tar.gz'), dest=dest_dir)
            os.system('rm -rf ' + os.path.join(
                dest_dir, 'autotest_result.tar.gz'))
            # Copying avocado results
            if avtest:
                dest_av = os.path.join(
                    result_path, 'kernelOrg_' + datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '_avocado')
                os.makedirs(dest_av)
                tar_in_host(
                    obj, console, tag='avocado', path=commonlib.avocado_result)
                scp_from_host(
                    host_details, dest_av, files='avocado_result.tar.gz')
                commonlib.untar(
                    os.path.join(dest_av, 'avocado_result.tar.gz'), dest=dest_av)
                os.system('rm -rf ' + os.path.join(
                    dest_av, 'avocado_result.tar.gz'))
                obj.run_cmd(commonlib.avocado_clean, console)
            tear_down(obj, console)
        else:
            logging.error('Error with result generation')
            tear_down(obj, console)
        obj.close_console(console)


def run_function(obj, console, host_details, git, tests, bso_details, sid, components, hmc_flag=False):
    '''
    In PowerKVM or Power NV, Check for bso auth
    1. Clone the git.
    2. Do a kernel-build test
    3. Wait for login & Login
    4. Run --continue
    5. Return path of the html generated.
    '''
    clone_cmd = None
    if commonlib.repo == 'autotest':
        autotest_repo = commonlib.autotest_repo
    content = obj.run_cmd('git --version', console)
    if content[-1].split()[-1] < '1.8':
        git_cmd = 'git clone --recursive '
    else:
        git_cmd = 'git -c http.sslVerify=false clone --recursive '
    clone_cmd = git_cmd + autotest_repo + ' > /dev/null 2>&1'
    avocado_repo = git_cmd + commonlib.avocado_repo + ' > /dev/null 2>&1'

    commonlib.install_packages(obj, console)
    obj.bso_auth(console, bso_details['username'], bso_details['password'])
    result_path = None
    obj.run_cmd('uname -r', console)
    obj.run_cmd('cd', console)
    if check_ls(obj, console, 'avocado-fvt-wrapper'):
        obj.run_cmd(
            'rm -rf avocado-fvt-wrapper', console)
    obj.run_cmd(avocado_repo, console)

    if not check_ls(obj, console, 'avocado-fvt-wrapper'):
        logging.error("\nProblem in cloning avocado repo")
    obj.run_cmd('cd avocado-fvt-wrapper', console)
    obj.run_cmd(commonlib.avocado_clean, console)
    obj.run_cmd('cd /root/', console)

    logging.info('\nCloning %s', commonlib.repo)
    if check_ls(obj, console, commonlib.repo):
        obj.run_cmd(
            'rm -rf ' + commonlib.repo, console)
    obj.run_cmd(clone_cmd, console)
    cur_path = obj.run_cmd('pwd', console)
    base_path = os.path.join(cur_path[-1], commonlib.repo)

    if not check_ls(obj, console, commonlib.repo):
        logging.error("\nProblem in cloning %s repo", commonlib.repo)
        tear_down(obj, console)
        sys.exit(1)
    if commonlib.repo == 'autotest':
        obj.run_cmd('cd autotest; git apply /root/autotest.patch', console)
        obj.run_cmd(
            'cd client/tests; git apply /root/autotest-client-tests.patch', console)
        obj.run_cmd('cd', console)

    content_src = obj.run_cmd('ls /home/', console)
    for val in content_src:
        if 'linux_src' in val:
            obj.run_cmd('rm -rf /home/linux_src/', console)
    if git['kernel_config'] != '' and 'make' not in git['kernel_config'] :
        config_name = git['kernel_config'].rsplit('/', 1)[-1]
        git['kernel_config'] = config_name
    if git['patches'] != '':
        patch_name = git['patches'].rsplit('/', 1)[-1]
        git['patches'] = patch_name

    if tests:
        tests = "'" + tests + "'"
        build_cmd = './' + commonlib.repo + '/client/autotest-local ./' + commonlib.repo + '/client/tests/kernelorg/kernel-build.py --args "host_kernel=' + \
            git['host_kernel_git'] + ' host_kernel_branch=' + git['host_kernel_branch'] + \
            ' config_dir=' + git['kernel_config'] + ' patches=' + \
            git['patches'] + ' tests=' + tests + '"'
    else:
        build_cmd = './' + commonlib.repo + '/client/autotest-local ./' + commonlib.repo + '/client/tests/kernelorg/kernel-build.py --args "host_kernel=' + \
            git['host_kernel_git'] + ' host_kernel_branch=' + git['host_kernel_branch'] + \
            ' config_dir=' + git['kernel_config'] + \
            ' patches=' + git['patches'] + '"'

    build_result = obj.run_build(build_cmd, console)
    time.sleep(10)
    try:
        result_dir = commonlib.autotest_result
        junit = os.path.join(base_path, "client/tools/results2junit.py")
        junit_result = "%s/results.xml" % result_dir
        cmd = "%s %s > %s" % (junit, result_dir, junit_result)
        if build_result == 'build':
            obj.run_cmd(cmd, console)
            return (result_dir, None)
        elif build_result == 'kexec':
            login_result = obj.run_login(console)
            if login_result == 'Login':
                console.sendline(host_details['username'])
                if hmc_flag:
                    console.send('\r')
                rc = console.expect(
                    [r'[Pp]assword:', pexpect.TIMEOUT], timeout=120)
                time.sleep(5)
                if rc == 0:
                    console.sendline(host_details['password'])
                    if hmc_flag:
                        console.send('\r')
                else:
                    tear_down(obj, console)
                    sys.exit(1)
            elif login_result == 'Error':
                logging.error('Error before kexec...')
                tear_down(obj, console)
                sys.exit(1)
            else:
                console.expect(pexpect.TIMEOUT, timeout=30)
                logging.error('Error before logging in..')
                tear_down(obj, console)
                sys.exit(1)
        elif build_result == 'report':
            logging.error(' Error in kernel building')
            obj.run_cmd(cmd, console)
            return (result_dir, None)
        else:
            logging.error('Error before kexec')
            tear_down(obj, console)
            sys.exit(1)
    except pexpect.ExceptionPexpect, e:
        console.sendcontrol("c")
        console.expect(pexpect.TIMEOUT, timeout=60)
        logging.info("%s", console.before)

    rc = console.expect(['Last login:', 'incorrect'], timeout=300)
    time.sleep(5)
    if rc == 0:
        console.sendline('PS1=[pexpect]#')
        if hmc_flag:
            console.send('\r')
        rc = console.expect_exact('[pexpect]#')
        if rc == 0:
            logging.info(' Shell prompt changed')
        else:
            tear_down(obj, console)
            sys.exit(1)
        logging.info("Enable kernel ftrace:")
        obj.run_cmd('sysctl -w kernel.ftrace_dump_on_oops=1', console)
        continue_result = obj.run_cmd(
            commonlib.continue_cmd, console, timeout=commonlib.test_timeout)
        if 'Report successfully' in continue_result[-1]:
            result_path = commonlib.autotest_result
            junit = os.path.join(base_path, "client/tools/results2junit.py")
            junit_result = "%s/results.xml" % result_path
            cmd = "%s %s > %s" % (junit, result_path, junit_result)
            obj.run_cmd(cmd, console)
        else:
            result_path = commonlib.autotest_result
            junit = os.path.join(base_path, "client/tools/results2junit.py")
            junit_result = "%s/results.xml" % result_path
            cmd = "%s %s > %s" % (junit, result_path, junit_result)
            obj.run_cmd(cmd, console)
            logging.error('Tests have taken more than %s seconds' %
                          commonlib.test_timeout)
            logging.info('Copying Existing reults')

        if components:
            obj.run_cmd(
                'mkdir -p /root/avocado-korg/', console)
            obj.run_cmd(
                'rm -rf /root/avocado-korg/*', console)
            obj.run_cmd('cd avocado-fvt-wrapper', console)

            # TODO: parallel_run for each_component
            for component in components.split(','):
                obj.run_cmd('mkdir -p /root/avocado-korg/' +
                            component, console)
                obj.run_cmd(commonlib.avocado_test_run % (
                    component, component), console, timeout=1000)
        else:
            logging.info("No avocado opeartion")

    elif rc == 1:
        logging.error("Error in host credentials")
        tear_down(obj, console)
        sys.exit(1)

    if result_path:
        return (result_path, commonlib.avocado_result)


def check_ipmi_details(details):
    if details['ip'] and details['password']:
        return True
    return False


def check_hmc_details(details):
    if details['ip'] and details['username'] and details['password'] and details['server'] and details['lpar']:
        return True
    return False


def check_host_details(details):
    if details['hostname'] and details['username'] and details['password']:
        return True
    return False


def scp_from_host(host_details, dest_dir, src_dir='/root', files='*'):
    logging.info("SCPing the files")
    logging.info('scp -l 8192 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r ' + host_details[
                 'username'] + '@' + host_details['hostname'] + ':' + src_dir + '/' + files + ' ' + dest_dir + '/')
    scp = pexpect.spawn('scp -l 8192 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r ' + host_details['username'] + '@' + host_details[
                        'hostname'] + ':' + src_dir + '/' + files + ' ' + dest_dir + '/')
    res = scp.expect([r'[Pp]assword:', pexpect.EOF])
    if res == 0:
        scp.sendline(host_details['password'])
        logging.info("Copying the results")
        scp.logfile = sys.stdout
        wait = scp.expect([pexpect.EOF], timeout=commonlib.scp_timeout)
        if wait == 0:
            logging.info('Files successfully copied')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ipmi", action="store", dest="ipmi", help="Specify the FSP/BMC ip,username and password\
                        Usage: --ipmi 'ip=fsp_ip,username=,password=password'")
    parser.add_argument("--hmc", action="store", dest="hmc", help="Specify the HMC ip, username, password, server_name in HMC, lpar_name in HMC\
                        Usage: --hmc 'ip=hmc_ip,username=hmc_username,password=hmc_password,server=server_name,lpar=lpar'")
    parser.add_argument("--host", action="store", dest="host", help="Specify the machine ip, linux username and linux password\
                        Usage: --host 'hostname=hostname,username=username,password=password'")
    parser.add_argument("--args", action="store", dest="args",
                        help="Specify the kernel git tree and kernel git branch Usage: --args 'host_kernel_git=git_link,host_kernel_branch=branch,kernel_config=configfile,patches=patchfile'")
    parser.add_argument("--tests", action="store", dest="tests", help="Specify the tests to perform\
                        Usage: --tests 'test_name1,test_name2,test_name3'")
    parser.add_argument("--list", action="store", dest="list", help="lists the tests available to run\
                        Usage: --list autotest or --list avocado")
    parser.add_argument("--disk", action="store", dest="disk", help="Specify the boot partition disk by-id\
                        Usage: --disk scsi-35000039348114000-part2")
    parser.add_argument("--bso", action="store", dest="bso", help="Specify the bso auth and password\
                        Usage: --bso username=user1@x.abc.com,password=password")
    parser.add_argument("--id", action="store", dest="id", help="[Optional] Specify the SIDfor CI run\
                        Usage: --id sid")
    parser.add_argument("--avtest", action="store", dest="avtest", help="[Optional] Specify the tests to perform in avocado\
                        Usage: --tests cpu,generic,io")

    options = parser.parse_args()
    machine_type = None
    host_details = None
    git = None
    tests = None
    disk = None
    sid = None
    logging.basicConfig(
        format='\n%(asctime)s %(levelname)s  |  %(message)s', level=logging.DEBUG, datefmt='%I:%M:%S %p')

    if options.list:
        test_list = options.list
        if 'autotest' in test_list:
            testfile = 'lib/tests.autotest'
        elif 'avocado' in test_list:
            testfile = 'lib/tests.avocado'
        try:
            with open(testfile, 'r') as tests:
                testlist = tests.readlines()
                for test in testlist:
                    print test.replace('\n', '')
        finally:
            print "\nUsage: python run_test.py --list autotest\nUsage:   --tests ltp \n\t --tests 'ltp,fio,dbench,fsfuzzer'"
            tests.close()
            sys.exit(0)

    if options.avtest:
        print "ERROR:  No avocado support!!!"
        print "\nUsage: python run_test.py --list autotest\n"
        sys.exit(0)

    if options.host:
        logging.info('%s', options.host)
        host_details = commonlib.get_keyvalue(options.host)
        if not check_host_details(host_details):
            logging.error('Provide necessary host details')
            sys.exit(1)
    else:
        logging.error('Provide host details')
        sys.exit(1)
    if options.bso:
        bso_details = commonlib.get_keyvalue(options.bso)
    else:
        logging.error('Specify bso details')
        sys.exit(1)

    if options.ipmi and options.hmc:
        logging.error('Specify only one type of arguement')
        sys.exit(1)
    elif options.ipmi:
        machine_type = 'Power KVM/NV'
        logging.info('Passing BSO for %s', host_details['hostname'])
        bso_authenticator.pass_bso(host_details['hostname'], user=bso_details[
                                   'username'], password=bso_details['password'])
    elif options.hmc:
        machine_type = 'Power VM'
    else:
        logging.error('Specify atleast one type of arguement')
        sys.exit(1)

    if options.disk:
        disk = options.disk
    else:
        logging.error("Disk not specified. Please specify a disk")
        sys.exit(1)

    if options.args:
        git = commonlib.get_keyvalue(options.args)
    else:
        logging.error("Provide git tree, branch")
        sys.exit(1)

    if options.tests:
        tests = options.tests
    else:
        logging.warning("Tests not specified. Performing kernel build only")

    if not options.avtest:
        logging.info("No avocado tests to perform")

    if options.id:
        sid = options.id

    if machine_type == 'Power KVM/NV':
        # 1. Get ipmi console
        # 2. run function with IPMI object,console
        # 3. copy the results the consoles
        # 4. Close the console

        details = commonlib.get_keyvalue(options.ipmi)
        is_up = os.system('ping -c 1 ' + details['ip'])
        if not is_up == 0:
            logging.error('System is down !')
        else:
            if check_ipmi_details(details):
                if not details['username']:
                    details['username'] = ''
                ipmi_reb = ipmi.ipmi(
                    details['ip'], details['username'], details['password'])
                logging.info("REBOOTING THE MACHINE")
                ipmi_reb.handle_reboot(disk, host_details)
                logging.info("REBOOT COMPLETE")
                time.sleep(10)
                if options.id:
                        scplib.scp_id(options.id, host_details)
                else:
                        scplib.scp_manual(git['kernel_config'], git['patches'], host_details)
                logging.info('Copying git patches')
                if commonlib.repo == 'autotest':
                    commonlib.scp_to_host('' + os.path.join(file_path, 'patches/autotest.patch') + ' ' + os.path.join(
                        file_path, 'patches/autotest-client-tests.patch'), host_details)
                logging.info("SCP COMPLETE")
                ipmi_obj = ipmi.ipmi(
                    details['ip'], details['username'], details['password'])
                con = ipmi_obj.getconsole()
                ipmi_obj.set_unique_prompt(
                    con, host_details['username'], host_details['password'])
                handle_console(
                    ipmi_obj, con, host_details, git, tests, bso_details, sid, options.avtest)
            else:
                logging.error('Specify necessary details of IPMI')
    elif machine_type == 'Power VM':
        # 1. Get HMC console
        # 2. Get LPAR console
        # 3. Run function with HMC object, console
        # 4. Copy the results back
        # 5. Close the consoles

        details = commonlib.get_keyvalue(options.hmc)
        if not details['username']:
            details['username'] = ''

        reboot_obj = hmc.hmc(
            details['ip'], details['username'], details['password'])
        reboot_obj.login()
        logging.info(" REBOOTING MACHINE")
        reb_result = reboot_obj.handle_reboot(
            disk, details['server'], details['lpar'])
        if reb_result == "Login":
            logging.info("SYSTEM REBOOTED")
        time.sleep(20)

        if options.id:
            scplib.scp_id(options.id, host_details)
        else:
            scplib.scp_manual(git['kernel_config'], git['patches'], host_details)
        logging.info('Copying git patches')
        if commonlib.repo == 'autotest':
            commonlib.scp_to_host('' + os.path.join(file_path, 'patches/autotest.patch') + ' ' + os.path.join(
                file_path, 'patches/autotest-client-tests.patch'), host_details)
        logging.info("SCP COMPLETE")

        logging.info("Passing BSO for %s", host_details['hostname'])
        bso_authenticator.pass_bso(host_details['hostname'], user=bso_details[
                                   'username'], password=bso_details['password'])

        mk = hmc.hmc(details['ip'], details['username'], details['password'])
        is_up = os.system('ping -c 1 ' + details['ip'])
        if not is_up == 0:
            logging.info('System is down !')
        else:
            if check_hmc_details(details):
                logging.info('System is up !')
                mk.login()
                console = mk.get_lpar_console(details['username'], details['password'], details[
                                              'server'], details['lpar'], host_details['username'], host_details['password'])
                mk.set_unique_prompt(console)
                handle_console(mk, console, host_details, git,
                               tests, bso_details, sid, options.avtest, hmc_flag=True)
            else:
                logging.error('Specify necessary HMC details')

if __name__ == '__main__':
    main()
