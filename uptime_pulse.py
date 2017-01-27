'''
    Test: Pulse Uptime Test
    Suggested Icon: schedule
    Description: 
        This test tests to see if a hardware or Linux Virtual Pulse has re-started.  It is a handy tool to track Pulse uptime, if you believe
        a Pulse is having issues and re-starting.  But, it could be altered to be useful on any server that should not be going down
        often.

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        uptime          min         0           0/60/30/999999              True        Minutes since the last re-boot

    Chart Settings:
        Y-Axis Title:   Uptime
        Chart Type:     Line
        Chart Stacking: No stacking (overlaid)

    Test Instance Template:
        NAME            TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        --------------- ----------- ------- ----------------------- ---------------------------------------------------
        -- NONE --

'''
from datetime import datetime
import os.path
import json
import time


def uptime_hw():

    results = {'availability': 0, 'uptime': -1}

    with open('/opt/ntct/gemini/gemini_monitor.log', 'r') as f:
        content = f.readlines()
    f.close()

    last_start = 'not_found'
    for line in content:
        if line.find('Gemini started') == -1:
            continue
        last_start = line

    if last_start != 'not_found':
        year = 2000+int(last_start[0:2])
        month = int(last_start[3:5])
        day = int(last_start[6:8])
        hour = int(last_start[9:11])
        minu = int(last_start[12:14])
        restart_time = datetime(year,month,day,hour,minu)
        restart_ts   = time.mktime(restart_time.timetuple())
        current_time = datetime.now()
        current_ts   = time.mktime(current_time.timetuple())
        time_diff_minute = (current_ts - restart_ts) / 60
        results['uptime'] = time_diff_minute
        results['availability'] = 1

    return results


def uptime():
    if os.path.isfile('/opt/ntct/gemini/gemini_monitor.log'):
        return uptime_hw()
    else:
        return {'availability': 0, 'uptime': -1}

def run(test_config):
    return json.dumps(uptime())
