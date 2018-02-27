import os
import sys
import socket
import struct
import select
import time
import datetime
import json
from time import sleep

'''
    Test: Tests the latency between a nPoint and a target device. 
    Suggested Icon: transform
    Status: Development
    Description: 
		Because MOS should be applied to VoIP packets only, the MOS output is an estimate of a VoIP call using the G.711 codec.
		
    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        availability
		lost_1																			Packet loss
		latency_min_1	msec		0													Minimum latency
		latency_avg_1	msec		0													Average latency
		latency_max_1	msec		0													Maximum latency
		jitter_1		msec		3													Jitter
		MOS_g711					2													MOS Score using G.711

    Chart Settings:
        Y-Axis Title:   Average latency
        Chart Type:     Line
        Chart Stacking: No stacking (overlaid)

   Test Instance Template:
        NAME               	TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        ------------------  ----------- ------- ----------------------- ---------------------------------------------------
        count				integer				5						Number of packet to send
		dest_addr			text				50						Target host for the test
		timeout				integer				1						Timeout for the test
'''

############################## INPUT ##############################
COUNT = "count"
DEST_ADDR = "dest_addr"
TIMEOUT = "timeout"

############################## OUTPUT #############################
LOST = "lost_1"
LATENCY_MIN = "latency_min_1"
LATENCY_AVG = "latency_avg_1"
LATENCY_MAX = "latency_max_1"
JITTER = "jitter_1"
MOS = "MOS_g711"

# From /usr/include/linux/icmp.h; your milage may vary.
ICMP_ECHO_REQUEST = 8

# Splitting up functions for better error reporting potential
# I'm not too confident that this is right but testing seems
# to suggest that it gives the same answers as in_cksum in ping.c
def checksum(source_string):
    sum = 0
    countTo = (len(source_string)/2)*2
    count = 0
    while count<countTo:
        thisVal = ord(source_string[count + 1])*256 + ord(source_string[count])
        sum = sum + thisVal
        sum = sum & 0xffffffff # Necessary?
        count = count + 2
 
    if countTo<len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff # Necessary?
 
    sum = (sum >> 16)  +  (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
 
    # Swap bytes. Bugger me if I know why.
    answer = answer >> 8 | (answer << 8 & 0xff00)
 
    return answer
 
# Receive the ping from the socket 
def receive_one_ping(my_socket, ID, timeout):
    timeLeft = timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([my_socket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return
 
        timeReceived = time.time()
        recPacket, addr = my_socket.recvfrom(1024)
        icmpHeader = recPacket[20:28]
        type, code, checksum, packetID, sequence = struct.unpack(
            "bbHHh", icmpHeader
        )
        if packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent
 
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return
 
# send one ping to the dest_addr 
def send_one_ping(my_socket, dest_addr, ID):
    dest_addr  =  socket.gethostbyname(dest_addr)
 
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    my_checksum = 0
 
    # Make a dummy header with a 0 checksum.
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    bytesInDouble = struct.calcsize("d")
    data = (192 - bytesInDouble) * "Q"
    data = struct.pack("d", time.time()) + data
 
    # Calculate the checksum on the data and the dummy header.
    my_checksum = checksum(header + data)
 
    # Now that we have the right checksum, we put that in. It's just easier
    # to make up a new header than to stuff it into the dummy.
    header = struct.pack(
        "bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
    )
    packet = header + data
    my_socket.sendto(packet, (dest_addr, 1)) # Don't know about the 1
 
#  Returns either the delay (in seconds) or none on timeout
def do_one(dest_addr, timeout):
    icmp = socket.getprotobyname("icmp")
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    except socket.error, (errno, msg):
        if errno == 1:
            # Operation not permitted
            msg = msg + (
                " - Note that ICMP messages can only be sent from processes"
                " running as root."
            )
            raise socket.error(msg)
        raise # raise the original error
 
    my_ID = os.getpid() & 0xFFFF
 
    send_one_ping(my_socket, dest_addr, my_ID)
    delay = receive_one_ping(my_socket, my_ID, timeout)
 
    my_socket.close()
    return delay

# Main test
def launch_ping(count, dest_addr, timeout):
	results = {}
	results['availability'] = 1
	lost = 0        # Number of loss packets
	mos = 0         # Mean Opinion Score
	latency = []    # Delay values [MIN, MAX, AVG]
	jitter = []     # Jitter values [MAX, AVG]
	time_sent = []  # Timestamp when packet is sent
	time_recv = []  # Timestamp when packet is received
	
	for i in range(0, count):
		try:
			time_sent.append(int(round(time.time() * 1000)))
			
			d = do_one(dest_addr, timeout)
			
			if d == None:
				lost = lost + 1
				time_recv.append(None)
				continue
			else:
				time_recv.append(int(round(time.time() * 1000)))
		except:
			results['availability'] = 0 # Failure
	
		# Compute latency
		latency.append(time_recv[i] - time_sent[i])
		
		# Compute jitter with the previous packet
		if len(jitter) == 0:
			# First packet received, jitter = 0
			jitter.append(0)
		else:
			# Find previous received packet
			for h in reversed(range(0, i)):
				if time_recv[h] != None:
					break
			# Compute difference of relative transit times
			drtt = (time_recv[i] - time_recv[h]) - (time_sent[i] - time_sent[h])
			jitter.append(jitter[len(jitter) - 1] + (abs(drtt) - jitter[len(jitter) - 1]) / float(16))
	
		# Wait 100ms between IPSLA tests to avoid to send them to quickly
		sleep(0.1)
	
	# Compute MOS Score using a R factor for codec G.711
	if len(latency) > 0:
		EffectiveLatency = sum(latency) / len(latency) + max(jitter) * 2 + 10
		if EffectiveLatency < 160:
			R = 93.2 - (EffectiveLatency / 40)
		else:
			R = 93.2 - (EffectiveLatency - 120) / 10
			# Now, let's deduct 2.5 R values per percentage of packet loss
			R = R - (lost * 2.5)
		# Convert the R into an MOS value.(this is a known formula)
		results['MOS_g711'] = 1 + (0.035) * R + (.000007) * R * (R-60) * (100-R)
	# Returning the results
	results['lost_1'] = lost / float(count) * 100
	
	if len(latency) > 0:
		results['latency_min_1'] = min(latency)
		results['latency_max_1'] = max(latency)
		results['latency_avg_1'] = sum(latency) / len(latency)
		results['availability'] = 1
	else:
		results['availability'] = 0 # Failure
		
	if len(jitter) > 0:
		results['jitter_1'] = jitter[len(jitter) - 1] 
	
	return results

def run(test_config):
	config = json.loads(test_config)
	count = config['count']
	dest_addr = config['dest_addr']
	timeout = config['timeout']
	
	return json.dumps(launch_ping(count, dest_addr, timeout))

test_config = {
	'count' : 5,
	'dest_addr' : '8.8.8.8',
	'timeout' : 1
    }
	
results = run(json.dumps(test_config))
print(results) # we can verify on the nPoint this way