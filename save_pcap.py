<<<<<<< HEAD
#!/usr/bin/env python
# This program is sending PCAP to a destination probe
# INPUT :
#		interface
#		filename
# OUTPUT :
# 		PCAP file

import argparse
import pcap
from construct.protocols.ipstack import ip_stack

# Save the pcap stats in a file
def save_pcap_stats(pktlen, data, timestamp):
	if not data:
		return
		
	stack = ip_stack.parse(data)
	payload = stack.next.next.next
	print payload
	with open("trace.pcap", "a") as trace_file:
		trace_file.write(payload)
		
# Main program
def main():
	# setup command line arguments
	parser = argparse.ArgumentParser(description = 'Packet Sniffer')
	parser.add_argument('--iface', action = "store", dest = "iface", default = 'eth0')
	parser.add_argument('--file', action = "store", dest = "file", default = "trace.pcap")
	
	# parse arguments
	given_args = parser.parse_args()
	iface, file = given_args.iface, given_args.file
	
	# start sniffing
	pc = pcap.pcapObject()
	pc.open_live(iface, 1600, 0, 100)
	
	try:
		while True:
			pc.dispatch(1, save_pcap_stats)
	except KeyboardInterrupt:
		print '%d packets received, %d packets dropped, %d packets dropped by the interface' % pc.stats()
	
if __name__ == '__main__':
=======
#!/usr/bin/env python
# This program is sending PCAP to a destination probe
# INPUT :
#		interface
#		filename
# OUTPUT :
# 		PCAP file

import argparse
import pcap
from construct.protocols.ipstack import ip_stack

# Save the pcap stats in a file
def save_pcap_stats(pktlen, data, timestamp):
	if not data:
		return
		
	stack = ip_stack.parse(data)
	payload = stack.next.next.next
	print payload
	with open("trace.pcap", "a") as trace_file:
		trace_file.write(payload)
		
# Main program
def main():
	# setup command line arguments
	parser = argparse.ArgumentParser(description = 'Packet Sniffer')
	parser.add_argument('--iface', action = "store", dest = "iface", default = 'eth0')
	parser.add_argument('--file', action = "store", dest = "file", default = "trace.pcap")
	
	# parse arguments
	given_args = parser.parse_args()
	iface, file = given_args.iface, given_args.file
	
	# start sniffing
	pc = pcap.pcapObject()
	pc.open_live(iface, 1600, 0, 100)
	
	try:
		while True:
			pc.dispatch(1, save_pcap_stats)
	except KeyboardInterrupt:
		print '%d packets received, %d packets dropped, %d packets dropped by the interface' % pc.stats()
	
if __name__ == '__main__':
>>>>>>> origin/master
	main()