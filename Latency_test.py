'''
    Test: Latency Test
    Suggested Icon: timer
    Description: 
	This test is meant to run on a HW pulse. It uses the popular 'MTR' network test utility to measure latency between a Pulse and a server.

        IMPORTANT:  This test is meant to run on a HW pulse.
		    To run it on a Virtual Pulse:
			1) install mtr on the HW pulse
			2) update the vraaibles MTR_BIN_PATH and MTR_FILES_DIR

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        avg             ms          3                                                   Average latency. No threshold should be configured.
        best            ms          3                                                   Best latency. No threshold should be configured.
        worst           ms          3           0/150/250/9999999                       Worst latency. Configure a threshold on this metric.

    Chart Settings:
        Y-Axis Title:   Latency
        Chart Type:     Line
        Chart Stacking: No stacking (overlaid)

    Test Instance Template:
        NAME            TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        --------------- ----------- ------- ----------------------- ---------------------------------------------------
        protocol        select      132                             Protocol. ICMP, UDP or TCP.
                        
                        OPTIONS: icmp (icmp), tcp (tcp), udp (udp)
                        
        count           number              5/1/30                  Number of packets to send
        server          text        50                              IP or host name of the server to measure latency to
'''
# this HW pulse script runs mtr against a host given in input
# for your reference the complete mtr result files are stored for
# 1 hour and can be retrieved with the pulse log files

import os
import time
import json
import re
import random

MTR_BIN_PATH = "/bin/mtr"

MTR_FILES_DIR = "/var/log"
MTR_BASE_OPTIONS = '-n -r'
KEEP_RESULT_FILES_FOR = 3600


def extract_stats(result_file):

    avg   = -1
    best  = -1
    worst = -1
    found = 0

    with open(result_file) as f:
        lines = f.readlines()

    last_line = lines[-1]

    if last_line.find('-- ???') == -1:
        m = re.search('\s+.\s+([0-9]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)',last_line)
        found += 1
        avg=m.group(3)
        best=m.group(4)
        worst=m.group(5)

    return found == 1, avg, best, worst


def run_mtr(server, protocol, count):

    if protocol=='udp':
        mtr_options = '--udp ' + MTR_BASE_OPTIONS
    elif protocol=='tcp':
        mtr_options = '--tcp ' + MTR_BASE_OPTIONS
    else: # default ICMP
        mtr_options = MTR_BASE_OPTIONS

    mtr_options += ' -c ' + count + ' ' + server

    random.seed()
    mtr_result_file = MTR_FILES_DIR + "/mtr_data_" + time.strftime("%H_%M_%S_") + str(random.randint(1,9999)) + ".txt"

    command = MTR_BIN_PATH + ' ' + mtr_options + ' > ' + mtr_result_file

    os.system(command)

    return mtr_result_file


def clean_up():
    now = time.time()
    cutoff = now - KEEP_RESULT_FILES_FOR
    files = os.listdir(MTR_FILES_DIR)
    for a_file_name in files:
        if a_file_name.startswith('mtr_data_'):
            the_file = MTR_FILES_DIR + "/" + a_file_name
            t = os.stat(the_file)
            c = t.st_ctime
            if c < cutoff:
                os.remove(the_file)


def driver(server, protocol, test_count):

    result={}
    result['avg'] = 0.0
    result['worst'] = 0.0
    result['best'] = 0.0
    result['availability'] = 0

    result_file = run_mtr(server,protocol,test_count)

    status, avg, best, worst = extract_stats(result_file)

    if status:
        result['avg'] = float(avg)
        result['best'] = float(best)
        result['worst'] = float(worst)
        result['availability'] = 1

    clean_up()

    return result


def run(test_config):
    config = json.loads(test_config)
    return json.dumps(driver(config['server'], config['protocol'], str(config['count'])))
