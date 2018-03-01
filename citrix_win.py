from __future__ import division
import os
import sys
from subprocess import check_output, Popen, PIPE, STDOUT
from os import path
import time
import json
import random
import string
from datetime import datetime

'''
	Test: Launch HDX session to a published resource through StoreFront or NetScaler Gateway (integrated with StoreFront).
	Suggested Icon: cast
	Status: Development
	Description: This script launches an HDX session to a published resource through StoreFront or NetScaler Gateway (integrated with StoreFront).

        It attempts to closely resemble what an actual user would do by:
        -Opening Internet Explorer.
        -Navigating directly to the Receiver for Web site or NetScaler Gateway portal.
        -Completing the fields.
        -Logging in.
        -Clicking on the resource.
        -Logging off the StoreFront site.

        Requirements:
        - Need to have CitrixSFLauncher.ps1 file deployed in the nPoint root installation directory
		-Use an Administrator console of PowerShell.
        -SiteURL should be part of the Intranet Zone (or Internet Zone at Medium-Low security) in order to be able to download AND launch the ICA file. This can be done through a GPO.
        -StoreFront 2.0 or higher.
        -If using NetScaler Gateway, version 9.3 or higher.
        -Changes in web.config under C:\inetpub\wwwroot\Citrix\<storename>Web\: autoLaunchDesktop to false, pluginAssistant to false and logoffAction to none.
        -Currently works for desktops or already subscribed apps only. You can auto subscribe users to apps by setting "KEYWORDS:Auto" in the published app's description.

        By default, the script creates a log file with the username like SFLauncher_username.log.
	
    Metrics:
        NAME            	UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        -------------------	----------- ----------- --------------------------- ----------- --------------------------------
        availability
        ctx_browser_time	seconds     3                                       N           Time to launch Internet Explorer and to get the connection page displayed
		ctx_connect_time	seconds		3										N			Connection time to Citrix StoreFront or NetScaler
		ctx_sf_time			seconds		3										N			Applications page displayed
		ctx_appli_time		seconds		3										N			Citrix application or VDI launching time
		
    Chart Settings:
        Y-Axis Title:   Response Time
        Chart Type:     Line
        Chart Stacking: Stacked (normal)

   Test Instance Template:
        NAME              			TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   	DESCRIPTION
        ------------------------	----------- ------- -------------------------- 	----------------------------------------------------------------------------------------------------------------
        SiteURL			  			text        100 			                	The complete URL of the StoreFront Receiver for Web site or NetScaler Gateway portal.
        UserName          			text        50                              	The name of the user which is used to log on. Acceptable forms are down-level logon name or user principal name.
        Password          			password    50                              	The password of the user which is used to log on.
        RessourceName	  			text	    50                              	The display name of the resource to be launched.
		SleepBeforeLogoff 			integer	    		5							The time in seconds to sleep after clicking the resource and before logging off.
		SleepBeforeEndingCitrix		integer				10							The time in seconds to sleep before ending the CItrix session.
		NumberOfRetries	  			integer	  			30 					    	The number of retries when retrieving an element.
		LogFilePath		  			text		50 		SystemDrive\Temp			Directory path to where the log file will be saved.
		LogFileName		  			text		50 		SFLauncher_<UserName>.log	File name for the log file.
		TwoFactorAuth     			text		50							  		The token or password used for two-factor authentication. This is used in the NetScaler Gateway portal.
'''

############################## INPUT ##############################
SITE_URL = "SiteURL"
USERNAME = "UserName"
PASSWORD = "Password"
RESSOURCE_NAME = "ResourceName"
SLEEP_BEFORE_LOGOFF = "SleepBeforeLogoff"
SLEEP_BEFORE_ENDING_CITRIX = "SleepBeforeEndingCitrix"
NUMBER_OF_RETRIES = "NumberOfRetries"
LOG_FILE_PATH = "LogFilePath"
LOG_FILE_NAME = "LogFileName"
TWO_FACTOR_AUTH = "TwoFactorAuth"

############################## OUTPUT #############################
BROWSER_TIME = "latency"
CONNECT_TIME = "connect_time"
RESSOURCE_TIME = "ressource_time"

###################################################################

# Splitting up functions for better error reporting potential
# Generate the batch command file to launch for Windows platform
def generate_win_batch_file(siteURL, username, password, ressource_name, sleep_before_logoff, sleep_before_ending_citrix, number_of_retries, log_file_path, log_file_name, two_factor_auth):
	status = False
	with open('CitrixSFLauncher.bat', 'w') as f:
		f.write("powershell.exe -executionpolicy remotesigned -File CitrixSFLauncher.ps1")
		f.write(' -siteURL ' + siteURL)
		f.write(' -UserName ' + username)
		f.write(' -Password ' + password)
		f.write(' -ResourceName ' + ressource_name)
		f.write(' -SleepBeforeLogoff ' + str(sleep_before_logoff))
		f.write(' -SleepBeforeEndingCitrix ' + str(sleep_before_ending_citrix))
		f.write(' -NumberOfRetries ' + str(number_of_retries))
		if log_file_path:
			f.write(' -LogFilePath ' + log_file_path)
		if log_file_name:
			f.write(' -LogFileName ' + log_file_name)
		if two_factor_auth:
			f.write(' -TwoFactorAuth ' + two_factor_auth)
		f.close
	status = True
	return status
	
# Launch the powershell script
def launch_powershell(siteURL, username, password, ressource_name, sleep_before_logoff, sleep_before_ending_citrix, number_of_retries, log_file_path, log_file_name, two_factor_auth):
	try:
		# Using subprocess gives you more versatility than os
		generate_win_batch_file(siteURL, username, password, ressource_name, sleep_before_logoff, sleep_before_ending_citrix, number_of_retries, log_file_path, log_file_name, two_factor_auth)
		command = 'CitrixSFLauncher.bat'
		p = Popen(command, shell = True, stdout = PIPE, stderr = PIPE)
		stdout, stderr = p.communicate()
		return stdout
	except: # Catch all the exception that exists
		return False # otherwhile we failed, return nothing

# Return the number of milliseconds between 2 dates
def seconds_between(d0, d1):
	d0 = datetime.strptime(d0, '%d/%m/%Y %H:%M:%S.%f')
	d1 = datetime.strptime(d1, '%d/%m/%Y %H:%M:%S.%f')
	delta = (abs((d1 - d0).seconds) * 1000) + (abs((d1 - d0).microseconds) / 1000)
	return delta
		
# Main function
def run_citrix(siteURL, username, password, ressource_name, sleep_before_logoff, sleep_before_ending_citrix, number_of_retries, log_file_path, log_file_name, two_factor_auth):
	results = {}
	results['availability'] = 0
	if os.name == 'nt':
		# For Windows, launch the powershell script
		output = launch_powershell(siteURL, username, password, ressource_name, sleep_before_logoff, sleep_before_ending_citrix, number_of_retries, log_file_path, log_file_name, two_factor_auth)
		if output:
			results['availability'] = 1
			results['is_pass'] = True
			# Parsing the output
			browser_t0 = output.split('Creating Internet Explorer COM object')
			browser_t1 = output.split('NETSCALER GATEWAY DETECTED')			
			tmp = browser_t0[1].split(' # ')
			t0 = tmp[0].split('\n')
			tmp = browser_t1[0].split(' # ')
			t1 = tmp[-2].splitlines(True)
			results['ctx_browser_time'] = float(seconds_between(t0[-1], t1[-1]) / 1000)
			connect_t0 = output.split('NETSCALER GATEWAY DETECTED')
			connect_t1 = output.split('Getting SF resources page')
			tmp = connect_t0[1].split(' # ')
			t0 = tmp[0].split('\n')
			tmp = connect_t1[0].split(' # ')
			t1 = tmp[-2].splitlines(True)
			results['ctx_connect_time'] = (seconds_between(t0[-1], t1[-1]) / 1000)
			sf_t0 = output.split('Getting SF resources page')
			sf_t1 = output.split('Getting resource')
			tmp = sf_t0[1].split(' # ')
			t0 = tmp[0].split('\n')
			tmp = sf_t1[0].split(' # ')
			t1 = tmp[-2].splitlines(True)
			results['ctx_sf_time'] = (seconds_between(t0[-1], t1[-1]) / 1000)
			appli_t0 = output.split('Getting resource')
			appli_t1 = output.split('Found wfica32.exe with PID')
			tmp = appli_t0[1].split(' # ')
			t0 = tmp[0].split('\n')
			tmp = appli_t1[0].split(' # ')
			t1 = tmp[-2].splitlines(True)						
			results['ctx_appli_time'] = (seconds_between(t0[-1], t1[-1]) / 1000)
		else:
			results['is_pass'] = False
			results['error'] = 'Error in powershell script'
	else:
		# to be developped later by running Citrix Receiver in command line mode for Linux
		results['error'] = 'test not yet compatible with the OS'
		results['is_pass'] = False
	
	return results

def run(test_config):
		config = json.loads(test_config)
		siteURL = config['siteURL']
		username = config['UserName']
		password = config['Password']
		ressource_name = config['RessourceName']
		sleep_before_logoff = config['SleepBeforeLogoff']
		sleep_before_ending_citrix = config['SleepBeforeEndingCitrix']
		number_of_retries = config['NumberOfRetries']
		log_file_path = config['LogFilePath']
		log_file_name = config['LogFileName']
		two_factor_auth = config['TwoFactorAuth']
		return json.dumps(run_citrix(siteURL, username, password, ressource_name, sleep_before_logoff, sleep_before_ending_citrix, number_of_retries, log_file_path, log_file_name, two_factor_auth))

# Test configuration
test_config = {
	'siteURL' : 'https://mycompany.com',
	'UserName' : 'CORP\user',
	'Password' : 'mypass',
	'RessourceName' : 'Putty',
	'SleepBeforeLogoff' : 5,
	'SleepBeforeEndingCitrix' : 10,
	'NumberOfRetries' : 30,
	'LogFilePath' : '',
	'LogFileName' : '',
	'TwoFactorAuth' : ''
	}

results = run(json.dumps(test_config))
print(results) # we can verify on the nPoint this way