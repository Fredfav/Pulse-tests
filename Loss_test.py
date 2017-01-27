'''
    Test: Loss Test
    Suggested Icon: power_input
    Description: 
        This test uses the popular 'MTR' network test utility to measure loss between a Pulse and a server.

        IMPORTANT:  Note that mtr must be installed on the PC with a Virtual Pulse.
                    It is not included in the Virutal Pulse installation.

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        loss            %           1           0/2/5/100                               Percentage of packets lost in test

    Chart Settings:
        Y-Axis Title:   Loss (%)
        Chart Type:     Line
        Chart Stacking: No stacking (overlaid)

    Test Instance Template:
        NAME            TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        --------------- ----------- ------- ----------------------- ---------------------------------------------------
        server          text        132                             IP or host name of the server to measure loss to
        protocol        text        50                              One of udp, tcp or icmp. Default is icmp.
        count           number              2/1/10                  Packets to send
'''
from subprocess import check_output
from os import path
import time
import json
import re
import random

MTR_BASE_OPTIONS = '-n -r'

# Note: the REGEX is ready to extract all values, even though this script only returns loss
MTR_REGEX = '([0-9]+).\|--\s((?:[0-9]{1,3}\.){3}[0-9]{1,3})\s+([0-9.]+)%\s+.\s+([0-9]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)'

random.seed()


def run_mtr(command):
    """
    Run the mtr utility - make retries if needed - return a status and the output of the command
    """

    mtr_ok = False
    try:
        mtr_output = check_output(command,shell=True)
    except:
        mtr_output = 'failed'
    else:
        lines = mtr_output.split('\n')
        lines.remove('')
        last_line = lines[-1]
        mtr_ok = last_line.find('-- ???') == -1

    return mtr_ok, mtr_output


def extract_stats(mtr_output):
    """
    Extract the loss out of the mtr output - the value of the last hop is the one that really matters
    If IP of the last hop is ??? then we fail the test as it means that the trace was not complete (or the
    final host did not answer)
    """
    loss = -1
    lines = mtr_output.split('\n')

    for idx in range(len(lines)-1,0,-1):
        line = lines[idx]
        if line.find('|--') == -1:
            continue # skip non result lines that might be at the end of the buffer
        # if the IP of the last line is ???, we fail the test (we did not get to our expected destination or
        # the host did not respond)
        if line.find('|-- ???') != -1:
            break
        m = re.search(MTR_REGEX,line)
        loss = float(m.group(3))
        break

    return loss


def select_mtr(server, protocol, count):
    """
    The mtr utility can be in a few locations, find where it is. Windows not in the current list
    """
    possible_paths = [ '/bin/mtr', '/usr/local/bin/mtr', '/usr/sbin/mtr', '/usr/bin/mtr' ]
    for a_possible_path in possible_paths:
        if path.exists(a_possible_path):
            mtr_path = a_possible_path
            break
    else:
        # set the path to mtr hoping it is in the path
        mtr_path = 'mtr'
    return mtr_path


def set_mtr_cmd_line_options(server, protocol, count):
    """
    Prepare the mtr command
    """
    if protocol == 'udp':
        mtr_options = ' -u ' + MTR_BASE_OPTIONS
    elif protocol == 'tcp':
        mtr_options = ' -T ' + MTR_BASE_OPTIONS
    else:  # default ICMP
        mtr_options = ' ' + MTR_BASE_OPTIONS

    mtr_options += ' -c ' + count + ' ' + server

    return mtr_options


def driver(server, protocol, test_count):
    """
    Schedule our test
    """
    # structure sent back to nGP
    result = {'loss': -1, 'availability': 0}

    mtr_path = select_mtr(server,str(protocol), test_count)
    if mtr_path == '':
        return result

    status, mtr_output = run_mtr(mtr_path + set_mtr_cmd_line_options(server, protocol, test_count))
    if not status:
        return result   # failure return without setting availability to 1

    result['loss'] = extract_stats(mtr_output)
    if result['loss'] == -1:
        return result   # failure return without setting availability to 1

    # all expected processing done, declare success
    result['availability'] = 1

    return result


def run(test_config):
    config = json.loads(test_config)
    return json.dumps(driver(config['server'], config['protocol'], str(config['count'])))
