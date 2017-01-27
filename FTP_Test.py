'''
    Test: FTP Test
    Suggested Icon: cloud_download
    Description: 
        This test logs into an FTP Server, and downloads a file in binary mode.  If the file is downloaded
        in less than 30sec, the test passes.  Login, and download time, as well as the data rate are reported by the script.
        The unit the data rate is reported in can be Mpbs or kpbs, as specified in the test configuration

        IMPORTANT: Note that the credentials appear in the nGP UI in plain text in this simple example script.  Ideally,
        the FTP server will accept annonymous users, and this isn't an issue.

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        connect_time    ms          2                          			        Time to login, in ms.
        transfer_time   ms          2           		                        Time to download the file, in ms.
        data_rate   	ms          2           999999/2/1		  	Yes     Data rate calculation, in Mpbs or kbps

    Chart Settings:
        Y-Axis Title:   Data Rate
        Chart Type:     Line
        Chart Stacking: No Stacking (overlaid)

    Test Instance Template:
        NAME            TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        --------------- ----------- ------- ----------------------- ---------------------------------------------------
        server          text        50                              FTP Server IP or host name
        username        text        50                              User name to log in as
        password        text        50                              Password to log in with
        filename        text        50                              File to download
        data_rate_unit  select	    n/a	    kpbs		    option names=kbps, Mpbs / option values: k, M

'''
import json
from ftplib import FTP
import time


def ftp_connect(server, username, password):
    ftp_handle = FTP(server)
    ftp_handle.login(username,password)
    return ftp_handle


def get_file(ftp_handle,filename):
    file_content = []
    ftp_handle.retrbinary('RETR ' + filename, file_content.append)
    return file_content


def driver(server, username, password,filename,data_rate_unit):
    result = { 'availability': 0, 'connect_time': 0, 'transfer_time': 0, 'data_rate': 0.0 }
    start_time = time.time()
    conn = ftp_connect(server, username, password)
    connect_time = time.time()
    result['connect_time'] = 100 * (connect_time - start_time)
    file_content = get_file(conn,filename)
    transfer_time = time.time()
    result['transfer_time'] = 100 * (transfer_time - connect_time)
    file_size = 0
    if len(file_content) >= 1:
        for data_piece in file_content:
            file_size += len(data_piece)
        transfer_duration = transfer_time-connect_time
        if data_rate_unit == 'k':
            result['data_rate'] = (file_size / transfer_duration) / 1e3
        elif data_rate_unit == 'M':
            result['data_rate'] = (file_size / transfer_duration) / 1e6
        result['availability'] = 1

    return result


def run(test_config):
    config = json.loads(test_config)
    print(config)
    return json.dumps(driver(config['server'], config['username'], config['password'], config['filename'], config['data_rate_unit']))

