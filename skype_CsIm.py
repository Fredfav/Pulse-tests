import os
import sys
from subprocess import check_output, Popen, PIPE, STDOUT
from os import path
import time
from time import sleep
import json
import random

'''
    Test: Tests the ability of two users to exchange instant messages.
    Suggested Icon: message
    Status: Development
    Description: Tests the ability of two users to exchange instant messages. This test is using a cmdlet introduced by Lync Server 2010.
	The prerequisites are the following ones:
		1. Skype powershell module are installed on the nPoint
		2. Set-ExecutionPolicy RemoteSigned is configured in Powershell

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
		WaitSeconds			integer										Specifies the amount of time (in seconds) that the system should wait for the Legal Intercept service to respond.
'''

############################## INPUT ##############################
TARGET_FQDN = "TargetFqdn"
RECEIVER_LOGIN = "ReceiverLogin"
RECEIVER_PASSWORD = "ReceiverPassword"
SENDER_LOGIN = "SenderLogin"
SENDER_PASSWORD = "SenderPassword"
SENDER_SIP_ADDRESS = "SenderSIPAddress"
RECEIVER_SIP_ADDRESS = "ReceiverSIPAddress"
WAIT_SECONDS = "WaitSeconds"

############################## OUTPUT #############################
LATENCY = "latency"

###################################################################

# Splitting up functions for better error reporting potential

# Generation of the powershell script to be executed
def create_powershell_script(target_fqdn, receiver_login, receiver_password, sender_login, sender_password, sender_sip_address, receiver_sip_address, wait_seconds):
	status = 0
	f = open('Test-CsIm.ps1', 'w')
	f.write('$User1 = "' + sender_login + '"\n')
	f.write('$Password1 = ConvertTo-SecureString -String "' + sender_password + '" -AsPlainText -Force\n')
	f.write('$cred1 = New-Object -TypeName "System.Management.Automation.PSCredential " -ArgumentList $User1, $Password1\n')
	f.write('$User2 = "' + receiver_login + '"\n')
	f.write('$Password2 = ConvertTo-SecureString -String "' + receiver_password + '" -AsPlainText -Force\n')
	f.write('$cred2 = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $User2, $Password2\n')
	f.write('Test-CsIm -TargetFqdn ' + target_fqdn + ' -SenderSipAddress "' +  sender_sip_address + '" -SenderCredential $cred1 -ReceiverSipAddress "' + receiver_sip_address + '" -ReceiverCredential $cred2 -OutLoggerVariable TestOutput\n')
	f.write('$TestOutput.ToXML() > Test-CsIm_Out.xml\n')
	f.close
	status = 1
	return status

# Launch the generated powershell script
def call():
		try :
				command = "powershell.exe -executionpolicy remotesigned -File " + 'Test-CsIm.ps1'
				#command = "dir"
				# Using subprocess gives you more versatility than os
				p = Popen(command, shell = True, stdout = PIPE, stderr = PIPE)
				stdout, stderr = p.communicate()
				print stdout
				return stdout # return our connection time
		except: # Catch the exceptions that exist (catch all)
				return 0 # otherwise we failed, return nothing

# Main function				
def skype_im(target_fqdn, receiver_login, receiver_password, sender_login, sender_password, sender_sip_address, receiver_sip_address, wait_seconds):
	results = {}
	results['availability'] = 0
	if os.name == 'nt':
		# Simplified process for determine test success or failure
		if create_powershell_script(target_fqdn, receiver_login, receiver_password, sender_login, sender_password, sender_sip_address, receiver_sip_address, wait_seconds):
			output = call()
			result = output.split('Result        : ')
			latency = output.split('Latency       : ')
			s = result[1].split('\r\n')
			if s[0] == "Success":
				results['availability'] = 1 # available!
			else:
				results['availability'] = 0 # Failure !!!
			s = latency[1].split('\r\n')
			results['latency'] = s[0] # to get the result in msec
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
	receiver_login = config['ReceiverLogin']
	receiver_password = config['ReceiverPassword']
	sender_login = config['SenderLogin']
	sender_password = config['SenderPassword']
	sender_sip_address = config['SenderSIPAddress']
	receiver_sip_address = config['ReceiverSIPAddress']
	wait_seconds = config['WaitSeconds']
	
	return json.dumps(skype_im(target_fqdn, receiver_login, receiver_password, sender_login, sender_password, sender_sip_address, receiver_sip_address, wait_seconds))

test_config = {
	'TargetFqdn' : 'skype.corp.cloud',
	'ReceiverLogin' : 'CORP\user1',
	'ReceiverPassword' : 'password1',
	'SenderLogin' : 'CORP\user2',
	'SenderPassword' : 'password2',
	'SenderSIPAddress' : 'user2@corp.cloud',
	'ReceiverSIPAddress' : 'user1@corp.cloud',
	'WaitSeconds' : 0
    }
	
results = run(json.dumps(test_config))
print(results) # we can verify on the nPoint this way