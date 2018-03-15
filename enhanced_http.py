import os
import json
import string
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

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
		
    Chart Settings:
        Y-Axis Title:   Response Time
        Chart Type:     Area
        Chart Stacking: Stacked (normal)

   Test Instance Template:
        NAME              			TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   	DESCRIPTION
        ------------------------	----------- ------- -------------------------- 	----------------------------------------------------------------------------------------------------------------
        SiteURL			  			text        100 			                	The complete URL of the StoreFront Receiver for Web site or NetScaler Gateway portal.
		basic_auth					boolean											If the web site need a basic authentication
        UserName          			text        50                              	The name of the user which is used to log on. Acceptable forms are down-level logon name or user principal name.
        Password          			password    50                              	The password of the user which is used to log on.
'''

############################## INPUT ##############################
SITE_URL = "SiteURL"
BASIC_AUTHENTICATION = "basic_auth"
USERNAME = "UserName"
PASSWORD = "Password"

############################## OUTPUT #############################
DOMAIN_LOOKUP = "domainLookup"
SECURE_CONNECTION = "secureConnection"
BACK_END = "back_end"
FRONT_END = "front_end"
LOAD_EVENT = "load_event"
TRANSACTION_TIME = "transaction_time"

###################################################################

# Splitting up functions for better error reporting potential
# Compute the performance data
def compute_perf(navigationStart, fetchStart, domainLookupStart, domainLookupEnd, connectStart, connectEnd, secureConnectionStart, requestStart, responseStart, responseEnd, domLoading, domComplete, loadEventStart, loadEventEnd):
	results = {}
	results['availability'] = 1
	results['domainLookup'] = domainLookupEnd - domainLookupStart
	if (secureConnectionStart == 0):
		results['secureConnection'] = 0
	else:
		results['secureConnection'] = requestStart - secureConnectionStart
	results['tcp_rtt'] = connectEnd - connectStart
	results['back_end'] = (responseEnd - navigationStart) - results['tcp_rtt']
	results['front_end'] = domComplete - domLoading
	results['transaction_time'] = domComplete - navigationStart
	if (loadEventStart == 0):
		results['load_event'] = 0
	else:
		results['load_event'] = loadEventEnd - loadEventStart
	return results

# Main function
def run_selenium(siteURL, basic_auth, username, password):
	results = {}
	chrome_options = Options()
	chrome_options.add_argument("headless")
	driver = webdriver.Chrome(chrome_options = chrome_options)
	if basic_auth:
		URL = siteURL + '/:'
		URL = URL + username
		URL = URL + '/:'
		URL = URL + password
		driver.get(URL)
	else:
		driver.get(siteURL)
	# Get performance data
	navigationStart = driver.execute_script("return window.performance.timing.navigationStart")    
	fetchStart =  driver.execute_script("return window.performance.timing.fetchStart")
	domainLookupStart = driver.execute_script("return window.performance.timing.domainLookupStart")
	domainLookupEnd = driver.execute_script("return window.performance.timing.domainLookupEnd")
	connectStart = driver.execute_script("return window.performance.timing.connectStart")
	connectEnd = driver.execute_script("return window.performance.timing.connectEnd")
	secureConnectionStart = driver.execute_script("return window.performance.timing.secureConnectionStart")
	requestStart = driver.execute_script("return window.performance.timing.requestStart")
	responseStart = driver.execute_script("return window.performance.timing.responseStart")
	responseEnd = driver.execute_script("return window.performance.timing.responseEnd")
	domLoading = driver.execute_script("return window.performance.timing.domLoading")
	domComplete = driver.execute_script("return window.performance.timing.domComplete")
	loadEventStart = driver.execute_script("return window.performance.timing.loadEventStart")
	loadEventEnd = driver.execute_script("return window.performance.timing.loadEventEnd")
	# Compute the performance indicators
	results = compute_perf(navigationStart, fetchStart, domainLookupStart, domainLookupEnd, connectStart, connectEnd, secureConnectionStart, requestStart, responseStart, responseEnd, domLoading, domComplete, loadEventStart, loadEventEnd)
	# Close the browser
	driver.close()
	return results

def run(test_config):
	config = json.loads(test_config)
	siteURL = config['siteURL']
	basic_auth = config['basic_auth']
	username = config['UserName']
	password = config['Password']
	return json.dumps(run_selenium(siteURL, basic_auth, username, password))

# Test configuration
test_config = {
	'siteURL' : 'https://www.yahoo.com/news/politics/',
	#'siteURL' : 'http://replybot.herokuapp.com/basic-auth', 
	'basic_auth' : False,
	'UserName' : 'user',
	'Password' : 'passwd'
}

#results = run(json.dumps(test_config))
#print(results) # we can verify on the nPoint this way