import os
import sys
from subprocess import check_output
from os import path
import time
import json
import random

'''
    Test: Skype call on a onPremise Skype for Business
    Suggested Icon: message
    Status: Development
    Description: Launch Skype and establish a call to a contact or a phone number, then close Skype.

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        availability
        conn_time        seconds     3           --                          N           Connexion Time

    Chart Settings:
        Y-Axis Title:   Connection Time
        Chart Type:     Line
        Chart Stacking: Stacked (normal)

   Test Instance Template:
        NAME            TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        --------------- ----------- ------- ----------------------- ---------------------------------------------------
        name_or_number  text        100     echo123                 Contact name or phone number to call
        username        text        100                             Skype username
        password        text        100                             Skype password
        call_duration   seconds     5       5                       Call test duration
'''

############################## INPUT ##############################
NAME_OR_NUMBER = "name_or_number"
USERNAME = "username"
PASSWORD = "password"
CALL_DURATION = "call_duration"

############################## OUTPUT #############################
CONN_TIME = "conn_time"

###################################################################

# Splitting up functions for better error reporting potential
def connect_to_skype(username, password):
		try :
				start_time = time.time()
				command = r"c:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\lync.exe username:" + username + " password:" + password
				# Using subprocess gives you more versatility than os
				#subprocess.call(["c:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\lync.exe", "username:" + username, "password:" + password])
				os.system(command)
				return time.time() - start_time # return our connection time
		except: # Catch the exceptions that exist (catch all)
				return 0 # otherwise we failed, return nothing

# Splitting up functions for better error reporting potential
def call(name_or_number):
        # The option to us is /callto:nameornumber to call the specified contact name or phone number
        try :
                command = r"c:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\lync.exe sip:" + name_or_number
                os.system(command)
                # Using subprocess gives you more versatility than os
                #subprocess.call(["c:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\lync.exe", "sip:" + name_or_number])
                # Call test duration
                time.sleep(call_duration)
                return True # return successful results
        except: # Catch the exceptions that exist (catch all)
                return False # return failure of function

# Splitting up functions for better error reporting potential
def shutdown_skype():
        try:
                # Shutdown Skype at the end of the test
                command = r"c:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\lync.exe /shutdown"
                os.system(command)
                # Using subprocess gives you more versatility than os
                #subprocess.call(["c:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\lync.exe", "shutdown"])
                return True # return successful results
        except: # Catch the exceptions that exist (catch all)
                return False # return failure of function
        

def skype_call(username, password, name_or_number, call_duration):
    results = {}
    results['availability'] = 0
    if os.name == 'nt':
        # Windows is using the following command : "c:\Program Files\Skype\Phone\Skype.exe
        # Skype should be added in the PATH variable
        # Connection to Skype using username and password

        # Simplified process for determine test success or failure
        
        results['conn_time'] = connect_to_skype(username, password)	
		
        if call(name_or_number) or shutdown_skype():
                results['availability'] = 1 # available!
                results['is_pass'] = True # success!
        else:
                results['is_pass'] = False # failure, don't change availability... :(
		
    else:
        # No more supported by Microsoft
        results['error'] = 'test not comptaible with the OS'
        results['is_pass'] = False
    return results

def run(test_config):
    config = json.loads(test_config)
    username = config['username']
    password = config['password']
    name_or_number = config['name_or_number']
    call_duration = config['call_duration']

    return json.dumps(skype_call(username, password, name_or_number, call_duration))

test_config = {
    'name_or_number' : 'echo123',
    'username' : 'student1@corp.cloud',
    'password' : 'password',
    'call_duration' : 5
    }
results = run(json.dumps(test_config))
print(results) # we can verify on the nPoint this way
