import os
import json
import string
import time
import uuid
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

'''
	Test: Launch a Web transaction and return enhanced response time (integrating AJAX and asynchronous transactions response time)
	Suggested Icon: open in browser
	Status: Development
	Description: This script launch a specific URL and return full detail response time.
    Requirements:
		Firefox needs to be installed
		Firefox binary need to be declared in the PATH env variable
	Logs:
    	None at this stage
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
		Timeout						integer											Maximum expected time to get the page available
'''

############################## GLOBAL CONSTANT ##############################
CHROME_PATH = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'
CHROMEDRIVER_PATH = 'C:/Python27/chromedriver'

###################################################################

# Splitting up functions for better error reporting potential
# Compute the performance data
def compute_perf(performance, availability, error):
	results = {}
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
	results['availability'] = availability
	results['error'] = error
	return results

# Retrieve the browser performance data
def browser_perf(self, start_time, availability, error):
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
	results = compute_perf(performance, availability, error)
	return results

# Generate manifest file for Chrome extension
def generate_manifest(directory):
	filename = os.path.join(directory, 'manifest.json')
	status = False
	with open(filename, 'w') as f:
		f.write('{\n')
		f.write('  "manifest_version": 2,\n')
		f.write('	"name": "Authentication for ...",\n')
		f.write('	"version": "1.0.0",\n')
		f.write('	"permissions": ["<all_urls>", "webRequest", "webRequestBlocking"],\n')
		f.write('	"background": {\n')
		f.write('		"scripts": ["background.js"]\n')
		f.write('	}\n')
		f.write('}\n')		
		f.close()
		status = True
	return status

# Generate Javascript exception file for Chrome
def generate_extension(directory, username, password):
	filename = os.path.join(directory, 'background.js')
	status = False
	with open(filename, 'w') as f:
		f.write('var username = "' + username + '";\n')
		f.write('var password = "' + password + '";\n')
		f.write('var retry = 3;\n')
		f.write('chrome.webRequest.onAuthRequired.addListener(\n')
		f.write('function handler(details) {   \n') 
		f.write('	if (--retry < 0)\n')
		f.write('		return {cancel: true};\n')
		f.write('	return {authCredentials: {username: username, password: password}};\n')
		f.write('},\n')
		f.write('{urls: ["<all_urls>"]},\n')
		f.write("['blocking']\n")
		f.write(');\n')
		status = True
	return status

# Generate the file for the authentication window
def mgmt_authentication(directory, username, password):
	if generate_manifest(directory) and generate_extension(directory, username, password):
		zip_filename = os.path.join(directory, 'background.zip')
		zip = zipfile.ZipFile(zip_filename, 'w')
		zip.write(os.path.join(directory, 'background.js'), 'background.js', compress_type = zipfile.ZIP_DEFLATED)
		zip.write(os.path.join(directory, 'manifest.json'), 'manifest.json', compress_type = zipfile.ZIP_DEFLATED)
		zip.close()
		status = True
	else:
		status = False
	return status

# Main function
def run_selenium(siteURL, authentication, username, password, ElementID, timeout):
	results = {}
	error = ''
	chrome_options = Options()
	#chrome_options.add_argument("headless")
	chrome_options.binary_location = CHROME_PATH
	if authentication:
		directory = os.path.join('', str(uuid.uuid4()))
		if not os.path.exists(directory):
			os.makedirs(directory)
		if mgmt_authentication(directory, username, password):
			availability = 1
			extension = os.path.join(directory, 'background.zip')
			chrome_options.add_extension(extension)
			driver = webdriver.Chrome(executable_path = CHROMEDRIVER_PATH, chrome_options = chrome_options)
		else:
			availability = 0
			error = 'Error in authentication'
	else:
		driver = webdriver.Chrome(executable_path = CHROMEDRIVER_PATH)
	StartTime = int(round(time.time() * 1000))
	# Authentication window management
	driver.get(siteURL)
	if ElementID:
		try:
			element = wait(driver, timeout).until(EC.presence_of_element_located((By.ID, ElementID)))
#			SearchItem = '//*[contains(text(),"' + ElementID + '")]'
#			print SearchItem
#			element = wait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, SearchItem)))
			availability = 1
		except:
			availability = 0
			error = 'Timeout in finding Element ID in the page'
		results = browser_perf(driver, StartTime, availability, error)
	else:
		results['availability'] = 0
		results['error'] = 'Element ID not defined'
	# Close the browser
	driver.close()
	if authentication:
		shutil.rmtree(directory)
	return results

def run(test_config):
	config = json.loads(test_config)
	siteURL = config['siteURL']
	authentication = config['authentication']
	username = config['UserName']
	password = config['Password']
	ElementID = config['ElementID']
	timeout = config['Timeout']
	return json.dumps(run_selenium(siteURL, authentication, username, password, ElementID, timeout))

# Test configuration	
test_config = {
	'siteURL' : 'http://replybot.herokuapp.com/basic-auth', 
	'authentication' : True,
	'UserName' : 'user',
	'Password' : 'passwd',
	'ElementID' : 'body', 
	'Timeout' : 30
}

results = run(json.dumps(test_config))
print(results) # we can verify on the nPoint this way