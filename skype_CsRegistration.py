import os
import sys
from subprocess import check_output, Popen, PIPE, STDOUT
from os import path
import time
from time import sleep
import json
import random

'''
    Test: Tests the ability of a user to log on to Skype for Business Server. .
    Suggested Icon: get app
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
		UserLogin		text		50									User login for the first of the two user accounts to be tested.
		UserPassword	password										User password for the first of the two user accounts to be tested
		UserSIPAddress	text		50									SIP address for the second of the two user accounts to be tested.
'''

############################## INPUT ##############################
TARGET_FQDN = "TargetFqdn"
USER_LOGIN = "UserLogin"
USER_PASSWORD = "UserPassword"
USER_SIP_ADDRESS = "UserSIPAddress"

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
	f.write('Test-CsRegistration -TargetFqdn "' + target_fqdn + '" -UserCredential $cred1 -UserSipAddress "' + user_sip_address + '" -OutLoggerVariable TestOutput2\n')
	f.write('$TestOutput2.ToXML() > Test-CsRegistration_Out.xml\n')
	f.close
	status = 1
	return status

# Launch the generated powershell script
def call():
		try :
				command = "powershell.exe -executionpolicy remotesigned -File " + 'Test-CsRegistration.ps1'
				#command = "dir"
				# Using subprocess gives you more versatility than os
				p = Popen(command, shell = True, stdout = PIPE, stderr = PIPE)
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
			print output
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
	user_login = config['UserLogin']
	user_password = config['UserPassword']
	user_sip_address = config['UserSIPAddress']
	
	return json.dumps(skype_registration(target_fqdn, user_login, user_password, user_sip_address))

test_config = {
	'TargetFqdn' : 'skype.corp.cloud',
	'UserLogin' : 'CORP\user1',
	'UserPassword' : 'password1',
	'UserSIPAddress' : 'user1@corp.cloud'
    }
	
results = run(json.dumps(test_config))
print(results) # we can verify on the nPoint this way