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
# Copyright: 2017 IBM
# Author: Abdul Haleem <abdhalee@linux.vnet.ibm.com>

import os
import sys
import datetime
import json
import fcntl
import errno
import time
sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from lib import common_lib as commonlib
from datetime import date

SID = ''
sidfile = commonlib.base_path + SID + '/' + SID + '.json'
date_str = datetime.datetime.now().strftime('%Y_%m_%d')
date_obj = datetime.datetime.strptime(date_str, '%Y_%m_%d')
TODAY = datetime.datetime.today().strftime('%A')

def form_sid(sid, mailid, git, branch, tests, avtest):
    git = git.split('/')[-2]
    mailid = mailid.split('@')[0]
    if tests:
        mean_sid = sid + '-' + mailid + '-' + git + \
            '-' + branch + '-' + tests.replace(',', '-')
    else:
        mean_sid = sid + '-' + mailid + '-' + git + '-' + branch + '-'
    if avtest:
        mean_sid += avtest.replace(',', '-')
    return mean_sid


def check_Qfile():
    '''
    This will check Q file in the path if present print the content
    else create a new q file
    '''
    if os.path.isfile(commonlib.schedQfile):
        print ("\nFile Exists !, Current Jobs in Queue....\n")
        print_Q()

    else:
        Qfile = open(commonlib.schedQfile, 'w')
        if os.path.isfile(commonlib.schedQfile):
            print (commonlib.schedQfile + ' Job file Created successfully !')
            Qfile.close()


def check_job_inQ(sid, mailid, git, branch, tests, avtest):
    '''
    Check if the given job is already in Q file
    else return Flase
    '''
    jobs = []
    while True:
        try:
            with open(commonlib.schedQfile, 'r') as Qfile:
                fcntl.flock(Qfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                jobs = Qfile.readlines()
                fcntl.flock(Qfile, fcntl.LOCK_UN)
            Qfile.close()
            for job in jobs:
                if form_sid(sid, mailid, git, branch, tests, avtest) == job.replace('\n', ''):
                    return True
            print (sid + "   Job Not in Queue !!")
            return False
        except IOError as ex:
            if ex.errno != errno.EAGAIN:
                raise "waiting for queue file to unlock"
        else:
            print ("waiting for queue file to unlock ... ")
            time.sleep(0.1)


def add_job_inQ(sid, mailid, git, branch, tests, avtest):
    '''
    Append the new jobs to the Q
    '''
    while True:
        try:
            with open(commonlib.schedQfile, 'a') as Qfile:
                fcntl.flock(Qfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                Qfile.write(form_sid(sid, mailid, git, branch, tests, avtest))
                Qfile.write('\n')
                fcntl.flock(Qfile, fcntl.LOCK_UN)
                Qfile.close()
                return
        except IOError as ex:
            if ex.errno != errno.EAGAIN:
                raise "waiting for queue file to unlock"
        else:
            print ("waiting for queue file to unlock ....")
            time.sleep(0.1)


def get_datafile_info(sid):
    '''
    for the given subscription id get me the data file path and information
    '''
    datafile = {}
    sidfile = commonlib.base_path + sid + '/' + sid + '.json'
    if os.path.isfile(sidfile):
        print (sidfile)
        datafile = commonlib.read_json(sidfile)
        return datafile
    else:
        print ("%s  Error : Datafile not Found !" % sidfile)
        return None


def update_datafile(sid, json_data):
    '''
    This will update the value of given key as json_data
    '''
    path = commonlib.base_path + sid + '/' + sid + '.json'
    if os.path.isfile(path):
        commonlib.update_json(path, json_data)

def get_subscrptn_date(sid):
    '''
    return the subscription date for the given sid
    '''
    dicts = {}
    subfile = commonlib.read_json(commonlib.base_path + 'subscribers.json')
    for dicts in subfile:
        if sid in dicts.values():
            subdate = datetime.datetime.now().strftime('%Y_%m_%d')
            if subdate < date_str:
                dicts['DATE'] = date_str
            return dicts['DATE']
    return None


def print_Q():
    '''
    List the waiting jobs in a Queue
    '''
    task = 0
    jobs = []
    if os.stat(commonlib.schedQfile).st_size != 0:
        while True:
            try:
                with open(commonlib.schedQfile, 'r') as Q:
                    fcntl.flock(Q, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    print (" ------------------------------------------------------------")
                    print ("| NO. |      SID's                                           |")
                    print (" ------------------------------------------------------------")
                    jobs = Q.readlines()
                    fcntl.flock(Q, fcntl.LOCK_UN)
                    Q.close()
                    for job in jobs:
                        task = task + 1
                        print ("   %s       %s" % (task, job.replace('\n', '')))
                    print ("-------------------------------------------------------------\n")
                    return
            except IOError as ex:
                if ex.errno != errno.EAGAIN:
                    raise
            else:
                print ("Waiting for queue file to unlock ...")
                time.sleep(0.1)
    else:
        print ("\nQueue File Empty  !!\n")


def main():
    sublist = []
    check_Qfile()
    sublist = commonlib.get_sid_list()
    for SID in sublist:
        json_data = get_datafile_info(SID)
        LASTRUN = json_data['LASTRUN']
        NEXTRUN = json_data['NEXTRUN']
        BUILDFREQ = json_data['BUILDFREQ']
        DATESUB = get_subscrptn_date(SID)
        MAILID = json_data['MAILID']
        TESTS = json_data['TESTS']
        AVTEST = json_data['AVTEST']
        GIT = json_data['URL']
        BRANCH = json_data['BRANCH']
        while not check_job_inQ(SID, MAILID, GIT, BRANCH, TESTS, AVTEST):

            if 'day' in BUILDFREQ:
                if LASTRUN is None or NEXTRUN is None:
                    json_data['LASTRUN'] = json_data['NEXTRUN'] = BUILDFREQ
                    update_datafile(SID, json_data)
                if BUILDFREQ == TODAY or NEXTRUN == TODAY :
                    add_job_inQ(SID, MAILID, GIT, BRANCH, TESTS, AVTEST)
                    if check_job_inQ(SID, MAILID, GIT, BRANCH, TESTS, AVTEST):
<<<<<<< HEAD
                        print SID + " Job added to Queue succesfully !"

=======
                        print (SID + " Job added to Queue succesfully !")
>>>>>>> 2330bf3 (Porting the jenkins-ci code from Python2 to Python3)
            else:
                if LASTRUN is None:
                    if BUILDFREQ == 'daily':
                        json_data['NEXTRUN'] = commonlib.oneday(date_str)
                    if BUILDFREQ == 'weekly':
                        json_data['NEXTRUN'] = commonlib.oneweek(date_str)
                    if BUILDFREQ == 'monthly':
                        json_data['NEXTRUN'] = commonlib.onemonth(date_obj)
                    update_datafile(SID, json_data)
<<<<<<< HEAD
                    print "always a candidate for Q"
                    add_job_inQ(SID, MAILID, GIT, BRANCH, TESTS, AVTEST)
                    if check_job_inQ(SID, MAILID, GIT, BRANCH, TESTS, AVTEST):
                        print SID + " Job added to Queue succesfully !"
=======
                    print ("always a candidate for Q")
                    add_job_inQ(SID, MAILID, GIT, BRANCH, TESTS, AVTEST)
                    if check_job_inQ(SID, MAILID, GIT, BRANCH, TESTS, AVTEST):
                        print (SID + " Job added to Queue succesfully !")
>>>>>>> 2330bf3 (Porting the jenkins-ci code from Python2 to Python3)
                else:
                    lastrun = datetime.datetime.strptime(LASTRUN, '%Y_%m_%d')
                    if NEXTRUN is not None:
                        nextrun = datetime.datetime.strptime(NEXTRUN, '%Y_%m_%d')
                    if lastrun > nextrun:
                        json_data['LASTRUN'] = date_str
                        update_datafile(SID, json_data)
                    if nextrun <= date_obj and lastrun != date_obj:
<<<<<<< HEAD
                        print "It is a candidate add for Q"
                        add_job_inQ(SID, MAILID, GIT, BRANCH, TESTS, AVTEST)
                        if check_job_inQ(SID, MAILID, GIT, BRANCH, TESTS, AVTEST):
                            print SID + " Job added to Queue succesfully !"
=======
                        print ("It is a candidate add for Q")
                        add_job_inQ(SID, MAILID, GIT, BRANCH, TESTS, AVTEST)
                        if check_job_inQ(SID, MAILID, GIT, BRANCH, TESTS, AVTEST):
                            print (SID + " Job added to Queue succesfully !")
>>>>>>> 2330bf3 (Porting the jenkins-ci code from Python2 to Python3)
                        if BUILDFREQ == 'daily':
                            json_data['NEXTRUN'] = commonlib.oneday(LASTRUN)
                        if BUILDFREQ == 'weekly':
                            json_data['NEXTRUN'] = commonlib.oneweek(LASTRUN)
                        if BUILDFREQ == 'monthly':
                            json_data['NEXTRUN'] = commonlib.onemonth(lastrun)
                        update_datafile(SID, json_data)
            break
    print ("\nList all jobs in Queue . . .  \n")
    print_Q()

if __name__ == '__main__':
    main()
