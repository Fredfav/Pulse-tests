import os
import sys
from subprocess import check_output, Popen, PIPE, STDOUT
from os import path
import time
from time import sleep
import json
import random

'''
    Test: Skype for Business Server : Audio Video Conference.
    Suggested Icon: video call
    Status: Development
    Description: Tests the ability of a pair of users to take part in an audio/video (A/V) conference. 
	This cmdlet was introduced in Lync Server 2010.
		The prerequisites are the following ones:
			1. Skype powershell module are installed on the nPoint
			2. Set-ExecutionPolicy RemoteSigned is configured in Powershell
			3. nPoint is 64 bits running on Windows

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        availability
		latency			msec		0													Latency of the script for the users to register on SfB and send IM messages

    Chart Settings:
        Y-Axis Title:   Latency
        Chart Type:     Line
        Chart Stacking: No stacking (overlaid)

   Test Instance Template:
        NAME               	TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        ------------------  ----------- ------- ----------------------- ---------------------------------------------------
        TargetFqdn			text		50								Fully qualified domain name (FQDN) of the pool to be tested.
		ReceiverLogin		text		50								User login for the first of the two user accounts to be tested.
		ReceiverPassword	password									User password for the first of the two user accounts to be tested
		SenderLogin			text		50								User login for the second of the two user accounts to be tested.
		SenderPassword		password									User password for the second of the two user accounts to be tested.
		SenderSIPAddress	text		50								SIP address for the second of the two user accounts to be tested.
		ReceiverSIPAddress	text		50
'''

############################## INPUT ##############################
TARGET_FQDN = "TargetFqdn"
RECEIVER_LOGIN = "ReceiverLogin"
RECEIVER_PASSWORD = "ReceiverPassword"
RECEIVER_SIP_ADDRESS = "ReceiverSIPAddress"
SENDER_LOGIN = "ReceiverLogin"
SENDER_PASSWORD = "ReceiverPassword"
SENDER_SIP_ADDRESS = "ReceiverSIPAddress"

############################## OUTPUT #############################
SFB_CS_AV_CONFERENCE = "SfB_CS_AV_CONFERENCE"

###################################################################

# Splitting up functions for better error reporting potential

# Generation of the powershell script to be executed
def create_powershell_script(target_fqdn, sender_login, sender_password, sender_sip_address, receiver_login, receiver_password, receiver_sip_address):
	status = 0
	f = open('Test-CsAVConference.ps1', 'w')
	f.write('$User1 = "' + sender_login + '"\n')
	f.write('$Password1 = ConvertTo-SecureString -String "' + sender_password + '" -AsPlainText -Force\n')
	f.write('$cred1 = New-Object -TypeName "System.Management.Automation.PSCredential " -ArgumentList $User1, $Password1\n')
	f.write('$User2 = "' + receiver_login + '"\n')
	f.write('$Password2 = ConvertTo-SecureString -String "' + receiver_password + '" -AsPlainText -Force\n')
	f.write('$cred2 = New-Object -TypeName "System.Management.Automation.PSCredential " -ArgumentList $User2, $Password2\n')
	f.write('Test-CsAVConference -TargetFqdn "' + target_fqdn + '" -SenderSipAddress "' + sender_sip_address + '" -SenderCredential $cred1 -ReceiverSipAddress "'+ receiver_sip_address +'" -ReceiverCredential $cred2 -OutLoggerVariable TestCsAVConference\n')
	f.write('$TestCsAVConference.ToXML() > Test-CsAVConference_Out.xml\n')
	f.close
	status = 1
	return status

# Launch the generated powershell script
def call():
		try :
				command = r"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -executionpolicy remotesigned -File " + 'Test-CsGroupIm.ps1'
				# Using subprocess gives you more versatility than os
				p = Popen(command, shell = True, stdout = PIPE, stderr = PIPE, cwd = os.getcwd())
				stdout, stderr = p.communicate()
				print stdout
				return stdout # return our connection time
		except: # Catch the exceptions that exist (catch all)
				return 0 # otherwise we failed, return nothing

# Main function				
def skype_cs_av_conference(target_fqdn, sender_login, sender_password, sender_sip_address, receiver_login, receiver_password, receiver_sip_address):
	results = {}
	results['availability'] = 0
	if os.name == 'nt':
		# Simplified process for determine test success or failure
		if create_powershell_script(target_fqdn, sender_login, sender_password, sender_sip_address, receiver_login, receiver_password, receiver_sip_address):
			output = call()
			result = output.split('Result        : ')
			latency = output.split('Latency       : ')
			s = result[1].split('\r\n')
			if s[0] == "Success":
				results['availability'] = 1 # available!
			else:
				results['availability'] = 0 # Failure !!!
			s = latency[1].split('\r\n')
			t = s[0].split(':') # to get the result in msec
			latency = float(t[2]) * 1000 + float(t[0]) * 3600000 + float(t[1]) * 60000
			results['SfB_CsAVConference'] = latency
			results['is_pass'] = True # success!
		else:
			results['error'] = ''
			results['is_pass'] = False
	else:
		# No more supported by Microsoft
		results['error'] = 'test not comptaible with the OS'
		results['is_pass'] = False	
	return results

def run(test_config):
	config = json.loads(test_config)
	target_fqdn = config['TargetFqdn']
	sender_login = config['SenderLogin']
	sender_password = config['SenderPassword']
	sender_sip_address = config['SenderSIPAddress']
	receiver_login = config['ReceiverLogin']
	receiver_password = config['ReceiverPassword']
	receiver_sip_address = config['ReceiverSIPAddress']
	
	return json.dumps(skype_cs_av_conference(target_fqdn, sender_login, sender_password, sender_sip_address, receiver_login, receiver_password, receiver_sip_address))

test_config = {
	'TargetFqdn' : 'skype.corp.cloud',
	'SenderLogin' : 'CORP\user1',
	'SenderPassword' : 'M3tr0logy',
	'SenderSIPAddress' : 'user1@corp.cloud',
	'ReceiverLogin' : 'CORP\user2',
	'ReceiverPassword' : 'M3tr0logy',
	'ReceiverSIPAddress' : 'user2@corp.cloud'
    }
	
results = run(json.dumps(test_config))
print(results) # we can verify on the nPoint this way