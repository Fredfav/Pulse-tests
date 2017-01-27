'''
    Test: Bandwidth
    Suggested Icon: import_export
    Description: 
        Performs a TCP bandwidth test using iPerf3 to any iPerf3 Server.  

        IMPORTANT:  1) Note that iPerf3 must be installed on the PC with a Virtual Pulse.
                       It is not included in the Virutal Pulse installation.

                    2) nGP does not include an iPerf3 Server. This must be set up seperatly.

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        sender          Mbps        1           0/200/100/999999            True        ??
        receiver        Mbps        1           0/200/100/999999            True        ??

    Chart Settings:
        Y-Axis Title:   Throughput
        Chart Type:     Line
        Chart Stacking: No stacking (overlaid)

    Test Instance Template:
        NAME            TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        --------------- ----------- ------- ----------------------- ---------------------------------------------------
        server          text        50                              IP or host name of the iPerf3 server
        port            text        50                              Port that iPerf3 is listening on
        test_duration   text        5                               Duration of the test, in seconds 
'''
from subprocess import check_output
from os import path
import time
import json
import re
import random

random.seed()


def run_iperf(command):
    iperf_output=['']
    returned_status=False
    retry=10
    iperf_ok = False
    while True:
        try:
            iperf_output = check_output(command,shell=True)
        except:
            iperf_output = 'failed'
        lines = iperf_output.split('\n')
        for line in lines:
            if line.find('iperf Done') != -1:
                iperf_ok = True
        if not iperf_ok:
            retry -= 1
            if retry==0:
                break
            sleep_duration = random.randint(1,6)
            time.sleep(sleep_duration)
        else:
            returned_status=True
            break

    return returned_status,iperf_output


def get_tcp_stats(iperf_output):
    sender = -1
    receiver = -1
    found = 0
    lines = iperf_output.split('\n')
    for line in lines:
        if line.find('sender') != -1:
            m = re.search('Bytes\s+([0-9.]+)',line)
            sender=float(m.group(1))
            giga = re.search('Bytes\s+[0-9.]+ Gbits',line)
            if giga:
                sender *= 1024
            kilo = re.search('Bytes\s+[0-9.]+ Kbits',line)
            if kilo:
                sender /= 1024
            found += 1
        if line.find('receiver') != -1:
            m = re.search('Bytes\s+([0-9.]+)',line)
            receiver=float(m.group(1))
            giga = re.search('Bytes\s+[0-9.]+ Gbits',line)
            if giga:
                receiver *= 1024
            kilo = re.search('Bytes\s+[0-9.]+ Kbits',line)
            if kilo:
                receiver /= 1024
            found += 1
    return found == 2, sender, receiver


def select_iperf_and_run(server,port,protocol,bandwidth,duration):
    status = False
    outbytes = ['']
    iperf_options = ' -c ' + server + ' -p ' + port + ' -t ' + str(duration)
    if protocol == 'udp':
        iperf_options += ' -u'
        iperf_options += ' -b' + str(bandwidth) + 'M'
    for possible_path in [ '/bin/iperf3', '/usr/local/bin/iperf3', '/usr/bin/iperf3' ]:
        if path.exists(possible_path):
            status, outbytes = run_iperf(possible_path + iperf_options)
            break
    else:
        # we did not find the binary in a known place, try with just the name, hoping it is in the PATH
        try:
            status, outbytes = run_iperf('iperf3' + iperf_options)
        except:
            pass

    return status, outbytes


def driver(server, port, protocol, bandwidth, test_duration):

    result = {}
    result['sender'] = 0.0
    result['receiver'] = 0.0
    result['availability'] = 0

    status, iperf_output = select_iperf_and_run(server,port,protocol,bandwidth,test_duration)
    if not status:
        return result

    status, sender, receiver = get_tcp_stats(iperf_output)
    if status:
        result['sender'] = sender
        result['receiver'] = receiver
        result['availability'] = 1

    return result


def run(testConfig):
    config = json.loads(testConfig)
    return json.dumps(driver(config['server'], config['port'], 'tcp', 'unused', config['test_duration']))

