from subprocess import check_output
from os import path
from math import pow
import time
import json
import re
import random
import socket, struct

MTR_BASE_OPTIONS = '-n -r' 
MTR_REGEX = '([0-9]+).\|--\s((?:[0-9]{1,3}\.){3}[0-9]{1,3})\s+([0-9.]+)%\s+.\s+([0-9]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)'

random.seed()

def ip2long(ip):
    """
    Convert an IP string to long
    """
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L", packedIP)[0]

def run_mtr(server,command):
    """
    Run the mtr utility - make retries if needed - return a status and the output of the command
    """
    mtr_output=['']
    returned_status=False
    mtr_ok = False
    retry=10
    while True:
        try:
            mtr_output = check_output(command,shell=True)
        except:
            mtr_output = 'failed'
        lines = mtr_output.split('\n')
        for line in lines:
            if (line.find('|-- ') != -1):
                # we hit an IP, so we have a result
                mtr_ok = True
                break
        if ( mtr_ok == False ):
            retry -= 1
            if ( retry==0 ):
                break
            sleep_duration = random.randint(1,6)
            time.sleep(sleep_duration)
        else:
            returned_status=True
            break
   
    return (returned_status,mtr_output)
      
def extract_stats(server,mtr_output):
    """
    Extract the AVG and hop count out of the mtr output - the AVG is the value of the last hop the one
    that really matter
    If IP of the last hop is ??? then we fail the test as it means that the trace was not complete (or the
    final host did not answer)
    """
    avg   = -1
    lines = mtr_output.split('\n')
    hops  = 0
    # count the hops and keep the avg of the last one
    for idx in range(len(lines)-1,0,-1):
        line = lines[idx]
        if (line.find('|--') == -1):
            continue # skip non result lines that might be at the end of the buffer
        # if the IP of the last line is ???, we fail the test (we did not get to our expected destination or the host did not respond)
        if (line.find('|-- ???') != -1):
            break
        m = re.search(MTR_REGEX,line)
        loss=float(m.group(3))
        hops=int(m.group(1))
        avg=float(m.group(6))
        worst=float(m.group(8))
        ip=m.group(2)
        desti_ip=ip2long(ip)
        break
    return loss
    
def select_mtr(server, protocol, count):
    """
    The mtr utility can be in a few locations, find where it is. Windows not in the current list
    """
 
    possible_paths = [ '/bin/mtr', '/usr/local/bin/mtr', '/usr/sbin/mtr', '/usr/bin/mtr' ]
    mtr_path = ''
    for a_possible_path in possible_paths:
        if path.exists(a_possible_path): 
            mtr_path = a_possible_path
            break
    return mtr_path

def set_mtr_cmd_line_options(server, protocol, count):
    """
    Prepare the mtr command
    """

    if (protocol=='udp'):
        mtr_options = ' -u ' + MTR_BASE_OPTIONS
    elif (protocol=='tcp'):
        mtr_options = ' -T ' + MTR_BASE_OPTIONS
    else: # default ICMP
        mtr_options = ' ' + MTR_BASE_OPTIONS

    mtr_options += ' -c ' + count + ' ' + server
        
    return mtr_options
    
def driver(server, protocol, test_count):
    """
    Schedule our test
    """

    # structure sent back to nGP
    result={ 'loss': -1, 'availability': 0 }

    mtr_path = select_mtr(server,str(protocol),test_count)
    if mtr_path == '':
        return result
     
    status, mtr_output = run_mtr(server, mtr_path + set_mtr_cmd_line_options(server, protocol, test_count))
    if (status == False):
        return result

    result['loss'] = extract_stats(server,mtr_output)
    if (result['loss'] == -1):
        return result

    # all expected processing done, declare success
    result['availability']=1

    return result


def run(testConfig):
    config = json.loads(testConfig)
    return json.dumps(driver(config['server'], config['protocol'], str(config['count'])))