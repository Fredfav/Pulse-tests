'''
    Test: Ping
    Suggested Icon: leak_add
    Description: 
        Performs a standard Ping to a remote server, and returns latency.  This test is useful to
        determine that a server is reachable and responding, and the latency between the client Pulse
        and the server.

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        ping_results    ms          0           0/100/500/30000                         Latency in milliseconds

    Chart Settings:
        Y-Axis Title:   ping
        Chart Type:     Line
        Chart Stacking: No stacking (overlaid)

    Test Instance Template:
        NAME            TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        --------------- ----------- ------- ----------------------- ---------------------------------------------------
        hostname        hostname                                    IP or host name of the server to ping
        timeout         integer             10/1/30/s               Time to wait before giving up on the ping response    
'''

def ping(hostname, timeout):
    if os.name == 'nt':
        # Windows has a different ping command than linux ping.
        # It takes timeout as milliseconds, not seconds
        command = ['ping', '-w', str(int(timeout) * 1000), '-n', '1', hostname]
    else:
        # Linux takes the timeout as seconds, which is what's shown in the UI
        command = ['ping', '-W', str(timeout), '-c', '1', hostname]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    results = process.stdout.read()

    # A generic-enough regex to get the ping time because windows reports it differently.
    p = re.compile(r'time(?:=|<)([\d\.]+)')
    matches = p.search(results)
    results = {}

    # If matches is not a truthy value, that means that the ping output did not have
    # "time" in the output, which means it likely failed.
    if matches:
        results['ping_results'] = matches.group(1)
    else:
        results['availability'] = 0
        results['error'] = 'ping failure'
    return results


def run(testConfig):
    config = json.loads(testConfig)
    hostname = config['hostname']
    timeout = config['timeout']
    return json.dumps(ping(hostname, timeout))