import socket
import json
import time

'''
    Test: Open Port Timing
    Suggested Icon: restore
    Description:
        This test times how long it takes to open a port

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        port_open_time  ms          1           0/200/500/99999               			Time taken to open the port, in ms.

    Chart Settings:
        Y-Axis Title:   Time to open
        Chart Type:     Line
        Chart Stacking: No Stacking (overlaid)

    Test Instance Template:
        NAME            TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        --------------- ----------- ------- ----------------------- ---------------------------------------------------
        server          hostname                                    FQN or IP of the server
        port            integer                                     port to open
'''


def open_port(host, port):
    results = {'time_to_open': -1, 'availability': 0}

    reference_time = time.time()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((host, port))
    socket_open_time = time.time()
    s.close()

    results['time_to_open'] = (socket_open_time - reference_time) * 1000
    results['availability'] = 1

    return results


def run(test_config):
    config = json.loads(test_config)
    host = config['hostname']
    port = config['port']
    return json.dumps(open_port(host, port))