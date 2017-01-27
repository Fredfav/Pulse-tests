<<<<<<< HEAD
import subprocess
import os
import re
import json

def ping(hostname, timeout, tos):
    if os.name == 'nt':
        # Windows has a different ping command than linux ping.
        # It takes timeout as milliseconds, not seconds
        command = ['ping', '-w', str(int(timeout) * 1000), '-n', '1', '-Q', str(tos), hostname]
    else:
        # Linux takes the timeout as seconds, which is what's shown in the UI
        command = ['ping', '-W', str(timeout), '-c', '1', '-Q', str(tos), hostname]
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
    tos = config['tos']
=======
import subprocess
import os
import re
import json

def ping(hostname, timeout, tos):
    if os.name == 'nt':
        # Windows has a different ping command than linux ping.
        # It takes timeout as milliseconds, not seconds
        command = ['ping', '-w', str(int(timeout) * 1000), '-n', '1', '-Q', str(tos), hostname]
    else:
        # Linux takes the timeout as seconds, which is what's shown in the UI
        command = ['ping', '-W', str(timeout), '-c', '1', '-Q', str(tos), hostname]
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
    tos = config['tos']
>>>>>>> origin/master
    return json.dumps(ping(hostname, timeout, tos))