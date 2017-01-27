#!/usr/bin/env python
# This program is sending PCAP to a destination probe
# INPUT :
# 		PCAP file 			(default: trace.pcap)
#		protocol 			(default: tcp))
#		destination IP 		(default: 10.10.10.10)
#		interface 			(default: eth0)
# OUTPUT :
# 		replay time
#		dropped packets

import os
import json
import sys
import re
import subprocess
import socket
import netifaces as ni
import argparse
from scapy.all import *

# Global variables
file = "trace.pcap"
protocol = "tcp"
dstip = "10.10.10.10"
iface = "eth0"
username = "root"

# Launch remote packet capture
def launch_remote():
	ret = subprocess.call(["ssh", username, "save_pcap.py"])
	return ret

# Retrieve the interface name
def retrieve_if():
	iface = ni.interfaces()
	return iface

# Retrieve the source IP
def retrieve_src_ip():
	host_name = socket.gethostname()
	source_ip = socket.gethostbyname(host_name)
	return source_ip

# Send the PCAP file accross the network
def send_packet(protocol=protocol, src_ip=retrieve_src_ip(), dst_ip=dstip, iface=None):
	if protocol == 'tcp':
		packet = IP(src=src_ip, dst=dst_ip)
	elif protocol == 'udp':
		packet = IP(src=src_ip, dst=dst_ip)
	else:
		raise Exception("Unknown protocol or not supported")
	
	send(packet, iface=iface)
	
# Stop the remote packet capture
def stop_capture():
	
	return 0

# Retrieve the stats from the target IP and the PCAP file
def retrieve_remote():
	
	return ret

# Launch the test
'''
def run(testConfig):
	config = json.load(testConfig)
	return json.dumps(driver(config['destination_IP'], config['protocole'], config['source_port'], 
		config['destination_port'], config['interface'], config['PCAP_file'], config['iteration']))
'''

def main():
	global file
	global protocol
	global dstip
	global srcport
	global dstport
	global iface
	global username
	
	# setup command line arguments
	parser = argparse.ArgumentParser(description = 'Packet Sniffer')
	parser.add_argument('--file', action = "store", dest = "file", default = "trace.pcap")
	parser.add_argument('--protocol', action = "store", dest = "protocol", default = "tcp")
	parser.add_argument('--dstip', action = "store", dest = "dstip", default = "10.10.10.10")
	parser.add_argument('--srcport', action = "store", dest = "srcport", default = "80")
	parser.add_argument('--dstport', action = "store", dest = "dstport", default = "80")
	parser.add_argument('--iface', action = "store", dest = "iface", default = 'eth0')
	
	
	# parse arguments
	given_args = parser.parse_args()
	iface, protocol, file = given_args.iface, given_args.protocol, given_args.file
	dstip = given_args.dstip
	
	# Global variables
	username = 'root@' + dstip

	launch_remote()	

if __name__ == '__main__':
	main()
