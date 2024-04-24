#!/usr/bin/env python3

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
# FIX ME
# Check out to given commit and create tar ball
# Check out to given tag and tar
# if a tree is based on the  other repository
# clone base and fetch the given git repostiory and merge

import os
import sys
import argparse
import logging
import subprocess
sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from lib import common_lib as commonlib


def cleanup(cur_path, tar_name, flag):
    logging.info('CLEAN UP PROCESS')
    if os.path.exists(cur_path + tar_name + '.tar.gz'):
        print(cur_path + tar_name + '.tar.gz')
        os.system('rm -rf ' + cur_path + tar_name + '.tar.gz')
    if os.path.exists(cur_path + tar_name):
        os.system('rm -rf ' + cur_path + tar_name)
    if flag:
        if os.path.exists(cur_path + 'hostCopy.tar.gz'):
            os.system('rm -rf ' + cur_path + 'hostCopy.tar.gz')
    if os.path.exists(cur_path + 'hostCopy'):
        os.system('rm -rf ' + cur_path + 'hostCopy')


def create_tar_copies(repo_path, hostcopy_path, tar_name):
    logging.info('Making a git copy')
    commonlib.tar(repo_path, tar_name)
    logging.info('Making a non .git copy')
    os.system('mv ' + repo_path + tar_name + ' ' + hostcopy_path)
    logging.info('Removing git files in host copy')
    os.system('rm -rf  ' + hostcopy_path + tar_name + '/.git')
    commonlib.tar(hostcopy_path, tar_name)
    os.system('rm -rf  ' + hostcopy_path + tar_name)


def clone_new_repo(path, git, branch, tar_name):
    if os.path.isdir(tar_name):
        os.system('rm -rf  ' + tar_name)
    os.chdir(path)
    logging.info("Fetching %s from branch %s", git, branch)
    cmd = 'git clone -b ' + branch + ' ' + git + ' ' + tar_name
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
        logging.info(
            "Unable to clone, Please check the access rights to %s", git)
        return False
    return True


def main():
    subscribers = []
    tar_json = {}
    check_flag = True
    repofile = commonlib.repo_path + 'repo.json'
    logging.basicConfig(
        format='\n%(asctime)s %(levelname)s  |  %(message)s', level=logging.DEBUG, datefmt='%I:%M:%S %p')
    parser = argparse.ArgumentParser()
    parser.add_argument("--git", action="store", dest="git",
                        help="Specify the git tree Usage: --git https://xyz.com/linux.git")
    parser.add_argument("--branch", action="store", dest="branch",
                        help="Specify the branch Usage: --branch master")
    parser.add_argument("--commit", action="store", dest="commit",
                        help="Specify the commit to checkout Usage: --commit 09d9c9491231")
    parser.add_argument("--tag", action="store", dest="tag",
                        help="Specify the tag to checkout  Usage: --commit 09d9c9491231")
    parser.add_argument("--base", action="store", dest="base",
                        help="To clone base repo and fetch the git repo  Usage: --base https://abc.com/linux.git")
    options = parser.parse_args()
    cur_path = commonlib.get_output('pwd') + '/'
    completion_json = commonlib.read_json(
        commonlib.base_path + 'completion.json')
    if not os.path.exists(commonlib.repo_path) or not os.path.exists(commonlib.hostcopy_path):
        os.system('mkdir ' + commonlib.repo_path)
        os.system('mkdir ' + commonlib.hostcopy_path)
        check_flag = False

    if not options.git and not options.branch:
        options.git = None
        options.branch = None

    if options.commit:
        commit = options.commit
    else:
        commit = None

    if options.tag:
        tag = options.tag
    else:
        tag = None

    if options.base:
        basegit = options.base
    else:
        basegit = None

    if not options.git and not options.branch:
        check_flag = True
        test_flag = True
        subscribers = commonlib.get_sid_list()
        for sid in subscribers:
            datafile = "%s/%s.json" % (sid, sid)
            sid_json = commonlib.read_json(
                os.path.join(commonlib.base_path, datafile))
            logging.info(":%s:", sid)
            tar_name = commonlib.tar_name(sid_json['URL'], sid_json['BRANCH'])
            tar_file = "%s%s.tar.gz" % (commonlib.repo_path, tar_name)
            head = 'git -C %s%s rev-parse HEAD' % (
                commonlib.repo_path, tar_name)
            if os.path.isfile(tar_file):
                logging.info("Linux tar found, Check for updates")
                os.chdir(commonlib.repo_path)
                commonlib.untar(tar_file)
                os.chdir(commonlib.repo_path + tar_name)
                sid_json['HEAD'] = commonlib.get_output(head)
                old_commit = commonlib.get_output('git log --format="%H" -n 1')
                new_commit = commonlib.get_output("git ls-remote " + sid_json[
                                                  'URL'] + " " + sid_json['BRANCH'] + " | head -n1 | awk '{print $1;}'")
                if old_commit != new_commit:
                    logging.info(
                        "Pulling latest code between <%s - %s>", old_commit, new_commit)
                    os.system('git config merge.renameLimit 999999')
                    cmd = 'git fetch origin && git reset --hard origin/%s' % sid_json[
                        'BRANCH']
                    status, output = commands.getstatusoutput(cmd)
                    if status != 0:
                        test_flag = False
                        logging.info(
                            "Problem in fetching latest code for %s:%s:%s", sid, sid_json['URL'], sid_json['BRANCH'])
                    sid_json['HEAD'] = commonlib.get_output(head)
                    os.chdir(commonlib.repo_path)
                    create_tar_copies(
                        commonlib.repo_path, commonlib.hostcopy_path, tar_name)
                else:
                    logging.info("No new commits ! Use existing tar")
                    os.system('rm -rf  ' + commonlib.repo_path + tar_name)
            else:
                logging.info("Tar not found !")
                logging.info(
                    "Cloning the new git repository for %s : %s", sid, tar_name)
                if not clone_new_repo(commonlib.repo_path, sid_json['URL'], sid_json['BRANCH'], tar_name):
                    logging.info(
                        "Unable to clone, Please check the access rights to %s", sid_json['URL'])
                    logging.info("Continue cloning other repos ..")
                    test_flag = False
                sid_json['HEAD'] = commonlib.get_output(head)
                create_tar_copies(
                    commonlib.repo_path, commonlib.hostcopy_path, tar_name)
                cleanup(cur_path, tar_name, check_flag)
            if test_flag:
                STATUS = 'PASS'
                logging.info("Tarring Complete for %s", tar_name)
            else:
                STATUS = 'FAIL'
                logging.info("Tarring fail for %s", tar_name)

            flag = False
            if os.path.isfile(repofile):
                for line in open(repofile, 'r').readlines():
                    if sid in line:
                        flag = True

            if flag:
                newlines = []
                commonlib.update_json(
                    os.path.join(commonlib.base_path, datafile), sid_json)
                for line in open(repofile, 'r').readlines():
                    if sid in line:
                        if STATUS != line.split(':')[-1]:
                            line = line.split(':')[:-1]
                            line.append(STATUS)
                            line = ':'.join(line) + '\n'
                    newlines.append(line)
                with open(repofile, "w") as fd:
                    for line in newlines:
                        fd.write(line)
                    fd.close()
            else:
                with open(repofile, "a") as fd:
                    fd.write(sid + ':' + tar_name + ':' + STATUS)
                    fd.write('\n')
                    fd.close()
        logging.info("\nFollowing repos updated:\n")
        for line in open(repofile, 'r').readlines():
            print(line.strip('\n'))

    else:
        check_flag = False
        logging.info("Preparing repo for manual runs")
        tar_name = commonlib.tar_name(options.git, options.branch)
        tar_file = commonlib.repo_path + tar_name + '.tar.gz'
        if os.path.isfile(tar_file):
            logging.info('Copying existing hostcopy tar to manual path')
            os.system('cp -f ' + commonlib.hostcopy_path +
                      tar_name + '.tar.gz  ' + cur_path)
            os.chdir(cur_path)
            commonlib.untar(tar_file)
            os.system('mv ' + tar_name + ' hostCopy')
            commonlib.tar(cur_path, 'hostCopy')
            cleanup(cur_path, tar_name, check_flag)
            logging.info("Tarring Complete ...!")
        else:
            logging.info("Tar not found !")
            logging.info("Cloning the new git repository .. ")
            clone_new_repo(
                commonlib.repo_path, options.git, options.branch, tar_name)
            create_tar_copies(
                commonlib.repo_path, commonlib.hostcopy_path, tar_name)
            logging.info("Tarring Complete ...!")
            cleanup(cur_path, tar_name, check_flag)
            return "trigger"

if __name__ == "__main__":
    main()
