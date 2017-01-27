'''
    Test: Port Availability Test (a.k.a TCP Port Open Test)
    Suggested Icon: track_changes
    Description: 
        This test tests to see if a specific port is open, or closed, on a specific server.  The most 
        common use would be to ensure that an application is up.  For example, is a SQL Server database
        up and responding on port 1433.

        It could also be used to ensure that a port is closed in a firewall.

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        port_open                   0                                                   Is the port open?  True if it is.

    Chart Settings:
        Y-Axis Title:   Port Open
        Chart Type:     Line
        Chart Stacking: No stacking (overlaid)

    Test Instance Template:
        NAME            TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        --------------- ----------- ------- ----------------------- ---------------------------------------------------
        hostname        hostname                                    Destination server IP or host name.
        port            integer                                     Port to test.
        desired_status  radio                                       Open/Closed options

                        OPTIONS:
                         open (open)
                         closed (closed)

'''
import socket
import json

def does_service_exist(host, port, desired_status):
    results = {}
    try:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, port))
            s.close()

        except socket.timeout as err:
            # Some sites will timeout if the port is closed.
            if desired_status == 'open':
                results['availability'] = 0
            else:
                results['availability'] = 1
            results['port_open'] = 0
            results['error'] = str(err)
            return results

        except socket.error as err:
            # While others will simply return a Connection Refused error.
            if err.errno == socket.errno.ECONNREFUSED:
                if desired_status == 'open':
                    results['availability'] = 0
                else:
                    results['availability'] = 1
                results['port_open'] = 0
                results['error'] = str(err)
                return results

            raise err

    except Exception as err:
        # If there is any failure case not caught above, probably indicates that
        # the host doesn't exist rather than the port being closed.
        if desired_status == 'open':
            results['availability'] = 0
        else:
            results['availability'] = 1
        results['port_open'] = 0
        results['error'] = str(err)
        return results

    if desired_status == 'open':
        results['availability'] = 1
    else:
        results['availability'] = 0
    results['port_open'] = 1
    return results


def run(testConfig):
    config = json.loads(testConfig)
    host = config['hostname']
    port = config['port']
    desired_status = config['desired_status']
    return json.dumps(does_service_exist(host, port, desired_status))