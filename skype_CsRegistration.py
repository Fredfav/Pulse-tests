import os
import sys
from subprocess import check_output, Popen, PIPE, STDOUT
from os import path
import time
from time import sleep
import json
import random

'''
    Test: Tests the ability of a user to log on to Skype for Business Server.
    Suggested Icon: message
    Status: Development
    Description: Tests the ability of a user to log on to Skype for Business Server. 
		The `Test-CsRegistration` cmdlet is a "synthetic transaction": a simulation of common Skype for Business Server activities used for health and performance monitoring. 
		This cmdlet was introduced in Lync Server 2010.
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
		SenderLogin			text		50								User login for the second of the two user accounts to be tested.
		SenderPassword		password									User password for the second of the two user accounts to be tested.
		SenderSIPAddress	text		50								SIP address for the second of the two user accounts to be tested.
		WaitSeconds			integer										Specifies the amount of time (in seconds) that the system should wait for the Legal Intercept service to respond.
'''

############################## INPUT ##############################
TARGET_FQDN = "TargetFqdn"
USER_LOGIN = "ReceiverLogin"
USER_PASSWORD = "ReceiverPassword"
USER_SIP_ADDRESS = "ReceiverSIPAddress"

############################## OUTPUT #############################
LATENCY = "latency"

###################################################################

# Splitting up functions for better error reporting potential

# Generation of the powershell script to be executed
def create_powershell_script(target_fqdn, user_login, user_password, user_sip_address):
	status = 0
	f = open('Test-CsRegistration.ps1', 'w')
	f.write('$User1 = "' + user_login + '"\n')
	f.write('$Password1 = ConvertTo-SecureString -String "' + user_password + '" -AsPlainText -Force\n')
	f.write('$cred1 = New-Object -TypeName "System.Management.Automation.PSCredential " -ArgumentList $User1, $Password1\n')
	f.write('Test-CsRegistration -TargetFqdn "' + target_fqdn + '" -UserCredential $cred1 -UserSipAddress "' + user_sip_address + '" -OutLoggerVariable TestRegistration\n')
	f.write('$TestRegistration.ToXML() > Test-CsRegistration_Out.xml\n')
	f.close
	status = 1
	return status

# Launch the generated powershell script
def call():
		try :
				command = r"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -executionpolicy remotesigned -File " + 'Test-CsRegistration.ps1'
				# Using subprocess gives you more versatility than os
				p = Popen(command, shell = True, stdout = PIPE, stderr = PIPE, cwd = os.getcwd())
				stdout, stderr = p.communicate()
				print stdout
				return stdout # return our connection time
		except: # Catch the exceptions that exist (catch all)
				return 0 # otherwise we failed, return nothing

# Main function				
def skype_registration(target_fqdn, user_login, user_password, user_sip_address):
	results = {}
	results['availability'] = 0
	if os.name == 'nt':
		# Simplified process for determine test success or failure
		if create_powershell_script(target_fqdn, user_login, user_password, user_sip_address):
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
			results['SfB_registration'] = latency
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
	user_login = config['UserLogin']
	user_password = config['UserPassword']
	user_sip_address = config['UserSIPAddress']
	
	return json.dumps(skype_registration(target_fqdn, user_login, user_password, user_sip_address))

test_config = {
	'TargetFqdn' : 'skype.corp.cloud',
	'UserLogin' : 'CORP\user1',
	'UserPassword' : 'M3tr0logy',
	'UserSIPAddress' : 'user1@corp.cloud'
    }
	
results = run(json.dumps(test_config))
print(results) # we can verify on the nPoint this way