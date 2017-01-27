<<<<<<< HEAD
import json
from ftplib import FTP
import time


def ftp_connect(server, username, password):
    ftp_handle = FTP(server)
    ftp_handle.login(username,password)
    return ftp_handle


def get_file(ftp_handle,filename):
    file_content = []
    ftp_handle.retrlines('RETR ' + filename, file_content.append)
    return file_content


def driver(server, username, password,filename,filesize):
    result = { 'availability': 0, 'connect_time': 0, 'transfer_time': 0 }
    start_time = time.time()
    conn = ftp_connect(server, username, password)
    connect_time = time.time()
    result['connect_time'] = 100 * (connect_time - start_time)
    file_content = get_file(conn,filename)
    result['transfer_time'] = 100 * (time.time() - connect_time)
    if len(file_content) == 1:
        if filesize==0:
            result['availability'] = 1
        else:
            if len(file_content[0]) == filesize:
                result['availability'] = 1

    return result


def run(test_config):
    config = json.loads(test_config)
=======
import json
from ftplib import FTP
import time


def ftp_connect(server, username, password):
    ftp_handle = FTP(server)
    ftp_handle.login(username,password)
    return ftp_handle


def get_file(ftp_handle,filename):
    file_content = []
    ftp_handle.retrlines('RETR ' + filename, file_content.append)
    return file_content


def driver(server, username, password,filename,filesize):
    result = { 'availability': 0, 'connect_time': 0, 'transfer_time': 0 }
    start_time = time.time()
    conn = ftp_connect(server, username, password)
    connect_time = time.time()
    result['connect_time'] = 100 * (connect_time - start_time)
    file_content = get_file(conn,filename)
    result['transfer_time'] = 100 * (time.time() - connect_time)
    if len(file_content) == 1:
        if filesize==0:
            result['availability'] = 1
        else:
            if len(file_content[0]) == filesize:
                result['availability'] = 1

    return result


def run(test_config):
    config = json.loads(test_config)
>>>>>>> origin/master
    return json.dumps(driver(config['server'], config['username'], config['password'], config['filename'], int(config['filesize'])))