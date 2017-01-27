# mtr-as.py
# this HW pulse script runs mtr against a host given in input
# for your reference the complete mtr result files are stored for
# 1 hour and can be retrieved with the pulse log files

import os
import time
import json
import re
import random

MTR_FILES_DIR = "/var/log"
MTR_BASE_OPTIONS = '-n -r -z' 
KEEP_RESULT_FILES_FOR = 3600

def extract_stats(result_file):

    found = 0
    AS = [0] * 20
    i = 0
	
    f = open(result_file)
    found += 1
    for line in f:
        if ( line.find('AS') != -1):
            m = re.search('\s+.\s+([0-9]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)', line)
            AS.insert(i, m.group(3))
            i += 1
                	
    return (found==1,AS[0], AS[1], AS[2], AS[3], AS[4], AS[5], AS[6], AS[7], AS[8], AS[9], AS[10], AS[11], AS[12], AS[13], AS[14], AS[15], AS[16], AS[17], AS[18], AS[19])

def run_mtr(server, protocol, count):

    status = False

    outbyte = ['']

    if (protocol=='udp'):
        mtr_options = ' --udp ' + MTR_BASE_OPTIONS
    elif (protocol=='tcp'):
        mtr_options = ' --tcp ' + MTR_BASE_OPTIONS
    else: # default ICMP
        mtr_options = ' ' + MTR_BASE_OPTIONS

    mtr_options += ' -c ' + count + ' ' + server
        
    random.seed()
    mtr_result_file = MTR_FILES_DIR + "/mtr_as_data_" + time.strftime("%H_%M_%S_") + str(random.randint(1,9999)) + ".txt"

    command = '/usr/bin/mtr' + mtr_options + ' > ' + mtr_result_file

    os.system(command)

    return mtr_result_file

def clean_up():
    now = time.time()
    cutoff = now - KEEP_RESULT_FILES_FOR
    files = os.listdir(MTR_FILES_DIR)
    for a_file_name in files:
        if a_file_name.startswith('mtr_as_data_'):
            the_file = MTR_FILES_DIR + "/" + a_file_name
            t = os.stat(the_file)
            c = t.st_ctime
            if c < cutoff:
                os.remove(the_file)

def driver(server, protocol, test_count):

    result={}
    result['as1']=0.0
    result['as2']=0.0
    result['as3']=0.0
    result['as4']=0.0
    result['as5']=0.0
    result['as6']=0.0
    result['as7']=0.0
    result['as8']=0.0
    result['as9']=0.0
    result['as10']=0.0
    result['as11']=0.0
    result['as12']=0.0
    result['as13']=0.0
    result['as14']=0.0
    result['as15']=0.0
    result['as16']=0.0
    result['as17']=0.0
    result['as18']=0.0
    result['as19']=0.0
    result['as20']=0.0
    result['availability']=0

    result_file = run_mtr(server,protocol,test_count)

    status, as1, as2, as3, as4, as5, as6, as7, as8, as9, as10, as11, as12, as13, as14, as15, as16, as17, as18, as19, as20 = extract_stats(result_file)

    if (status==True):
        result['as1']=float(as1)
        result['as2']=float(as2)
        result['as3']=float(as3)
        result['as4']=float(as4)
        result['as5']=float(as5)
        result['as6']=float(as6)
        result['as7']=float(as7)
        result['as8']=float(as8)
        result['as9']=float(as9)
        result['as10']=float(as10)
        result['as11']=float(as11)
        result['as12']=float(as12)
        result['as13']=float(as13)
        result['as14']=float(as14)
        result['as15']=float(as15)
        result['as16']=float(as16)
        result['as17']=float(as17)
        result['as18']=float(as18)
        result['as19']=float(as19)
        result['as20']=float(as20)
        result['availability']=1

    clean_up()
    
    return result


def run(testConfig):
    config = json.loads(testConfig)
    return json.dumps(driver(config['server'], config['protocol'], str(config['count'])))