import os
import json
import string
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

'''
	Test: Launch a Web transaction and return enhanced response time (integrating AJAX and asynchronous transactions response time)
	Suggested Icon: open in browser
	Status: Development
	Description: This script launch a specific URL and return full detail response time.

    Requirements:
	
	Logs:
    	
    Metrics:
        NAME            	UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        -------------------	----------- ----------- --------------------------- ----------- --------------------------------
        availability
        domainLookup		ms		    0                                       N           DNS query response time
		secureConnection	ms			0										N			SSL Handshake response time
		back_end			ms			0										N			Server + data network transfer time
		front_end			ms			0										N			browser processing time
		transaction_time	ms			0										N			overall transaction time
		load_event			ms			0										N			load event time for the current document
		overall_time		ms			0										N			Overall time for the page to be loaded and ready to use
		
    Chart Settings:
        Y-Axis Title:   Response Time
        Chart Type:     Area
        Chart Stacking: Stacked (normal)

   Test Instance Template:
        NAME              			TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   	DESCRIPTION
        ------------------------	----------- ------- -------------------------- 	----------------------------------------------------------------------------------------------------------------
        SiteURL			  			text        100 			                	The complete URL of the StoreFront Receiver for Web site or NetScaler Gateway portal.
		authentication				boolean											If the web site need a basic or NTLM authentication
        UserName          			text        50                              	The name of the user which is used to log on. Acceptable forms are down-level logon name or user principal name.
        Password          			password    50                              	The password of the user which is used to log on.
		ElementID					text		50									Element ID to find in the page
		ElementName					text		50									Element Name to find in the page
		Timeout						integer											Maximum expected time to get the page available
'''

############################## INPUT ##############################
SITE_URL = "SiteURL"
AUTHENTICATION = "basic_auth"
USERNAME = "UserName"
PASSWORD = "Password"
ELEMENT_ID = "Element_ID"
ELEMENT_NAME = "Element_Name"
TIMEOUT = "Timeout"

############################## OUTPUT #############################
DOMAIN_LOOKUP = "domainLookup"
SECURE_CONNECTION = "secureConnection"
BACK_END = "back_end"
FRONT_END = "front_end"
LOAD_EVENT = "load_event"
TRANSACTION_TIME = "transaction_time"
OVERALL_Time = "overall_time"

###################################################################

# Splitting up functions for better error reporting potential
# Compute the performance data
def compute_perf(performance):
	results = {}
#	results['availability'] = 1
	results['overallTime'] = performance['EndTime'] - performance['StartTime']
	results['domainLookup'] = performance['domainLookupEnd'] - performance['domainLookupStart']
	if (performance['secureConnectionStart'] == 0):
		results['secureConnection'] = 0
	else:
		results['secureConnection'] = performance['requestStart'] - performance['secureConnectionStart']
	results['tcp_rtt'] = performance['connectEnd'] - performance['connectStart']
	results['back_end'] = (performance['responseEnd'] - performance['navigationStart']) - results['tcp_rtt']
	results['front_end'] = performance['domComplete'] - performance['domLoading']
	results['transaction_time'] = performance['domComplete'] - performance['navigationStart']
	if (performance['loadEventStart'] == 0):
		results['load_event'] = 0
	else:
		results['load_event'] = performance['loadEventEnd'] - performance['loadEventStart']
	return results

# Retrieve the browser performance data
def browser_perf(self, start_time):
	performance = {}
	performance['StartTime'] = start_time
	# Retrieve the performance indicators from the browser
	performance['navigationStart'] = self.execute_script("return window.performance.timing.navigationStart")    
	performance['fetchStart'] =  self.execute_script("return window.performance.timing.fetchStart")
	performance['domainLookupStart'] = self.execute_script("return window.performance.timing.domainLookupStart")
	performance['domainLookupEnd'] = self.execute_script("return window.performance.timing.domainLookupEnd")
	performance['connectStart'] = self.execute_script("return window.performance.timing.connectStart")
	performance['connectEnd'] = self.execute_script("return window.performance.timing.connectEnd")
	performance['secureConnectionStart'] = self.execute_script("return window.performance.timing.secureConnectionStart")
	performance['requestStart'] = self.execute_script("return window.performance.timing.requestStart")
	performance['responseStart'] = self.execute_script("return window.performance.timing.responseStart")
	performance['responseEnd'] = self.execute_script("return window.performance.timing.responseEnd")
	performance['domLoading'] = self.execute_script("return window.performance.timing.domLoading")
	performance['domComplete'] = self.execute_script("return window.performance.timing.domComplete")
	performance['loadEventStart'] = self.execute_script("return window.performance.timing.loadEventStart")
	performance['loadEventEnd'] = self.execute_script("return window.performance.timing.loadEventEnd")
	performance['EndTime'] = int(round(time.time() * 1000))
	# Compute the performance indicators
	results = compute_perf(performance)
	return results

# Management of the authentication window
def mgmt_authentication(self, username, password):
	try:
		wait(self, 5).until(EC.alert_is_present())
		alert = self.switch_to_alert()
		alert.send_keys(username + Keys.TAB + password)
		alert.accept()
		status = True
	except TimeoutException:
		status = False
	return status

# Main function
def run_selenium(siteURL, authentication, username, password, element_id, element_name, timeout):
	results = {}
	StartTime = int(round(time.time() * 1000))
	caps = webdriver.DesiredCapabilities.FIREFOX
	caps["marionette"] = True
	driver = webdriver.Firefox(capabilities=caps)
	driver.get(siteURL)
	# Authentication window management
	if authentication:
		if mgmt_authentication(driver, username, password):
			results['availability'] = 1
		else:
			results['availability'] = 0
	if element_id or element_name:
		if element_id:
			try:
				element = wait(driver, timeout).until(EC.presence_of_element_located((By.ID, element_id)))
				results['availability'] = 1
			except:
				results['availability'] = 0
		elif element_name:
			try:
				element = wait(driver, timeout).until(EC.presence_of_element_located((By.NAME, element_name)))
				results['availability'] = 1
			except:
				results['availability'] = 0	
		results = browser_perf(driver, StartTime)
	else:
		results['availability'] = 0
	# Close the browser
	driver.close()
	return results

def run(test_config):
	config = json.loads(test_config)
	siteURL = config['siteURL']
	authentication = config['authentication']
	username = config['UserName']
	password = config['Password']
	element_id = config['Element_ID']
	element_name = config['Element_Name']
	timeout = config['Timeout']
	return json.dumps(run_selenium(siteURL, authentication, username, password, element_id, element_name, timeout))

# Test configuration
test_config = {
	'siteURL' : 'http://replybot.herokuapp.com/basic-auth', 
	'authentication' : True,
	'UserName' : 'username',
	'Password' : 'passwd',
	'Element_ID' : '',
	'Element_Name' : '',
	'Timeout' : 30
}

results = run(json.dumps(test_config))
print(results) # we can verify on the nPoint this way