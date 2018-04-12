import os
import json
import string
import time
import uuid
import zipfile
import shutil
import stopit
import logging
import chromedriver_binary
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
		Chrome driver needs to be installed
	Logs:
    	None at this stage
    Changes:
		v8:
			Linux platform compatibility
			Add the support of chromedriver_binary for the support of nPoint v2.6
			Timeout management
		v9:
			Logging capability
			Screenshot at the end of the test
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
		Logging						boolean											Log the results
		Screenshot					boolean											Generate a screenshot at the end of the test to see what is the browser behavior
'''
############################# OS DEPENDANT SETUP ############################
if os.name == 'posix':
	import signal
	from signal import SIGCHLD

############################## GLOBAL DECLARATION ##############################
if os.name == 'nt':
	CHROME_PATH = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'
	CHROMEDRIVER_PATH = 'C:/Python27/chromedriver.exe'
elif os.name == 'posix':
	from pyvirtualdisplay import Display
	CHROMEDRIVER_PATH = '/opt/ntct/gemini/chromium/bin/chrome'
	CHROME_PATH = '/opt/ntct/gemini/chromedriver'
else:
	CHROMEDRIVER_PATH = ''
	CHROME_PATH = ''
	
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

# Start Chrome driver
def start_chrome_driver(authentication, username, password):
	# Configure and start Chrome
	chrome_options = Options()
	# Use headless mode
	chrome_options.add_argument('no-sandbox')
	chrome_options.add_argument('start-maximized')	
	# OS dependant startup
	if os.name == 'nt':
		chrome_options.binary_location = CHROME_PATH
		display = ''
	elif os.name == 'posix':
		display = Display(visible = 0, size = (1024, 768))
		display.start()
		chrome_options.add_argument("--verbose")
		chrome_options.add_argument('--disable-gpu')
		chrome_options.add_argument('--lang=en')
	else: # Not supported
		driver = ''	
	if authentication:
		directory = os.path.join('', str(uuid.uuid4()))
		if not os.path.exists(directory):
			os.makedirs(directory)
		if mgmt_authentication(directory, username, password):
			availability = 1
			extension = os.path.join(directory, 'background.zip')
			chrome_options.add_extension(extension)
			if os.name == 'nt':
				driver = webdriver.Chrome(executable_path = CHROMEDRIVER_PATH, chrome_options = chrome_options)
			elif os.name == 'posix':
				driver = webdriver.Chrome(CHROME_PATH, chrome_options = chrome_options)
		else:
			availability = 0
			error = 'Error in authentication'
	else:
		directory = ''
		if os.name == 'nt':
			driver = webdriver.Chrome(executable_path = CHROMEDRIVER_PATH)
		elif os.name == 'posix':
			driver = webdriver.Chrome(CHROME_PATH, chrome_options = chrome_options)
	return directory, driver, display

# Exit Chrome driver
def close_chrome_driver(driver, authentication, directory, display):
	status = True
	driver.quit()
	# Cleanup authentication plugin files and directory
	if authentication:
		shutil.rmtree(directory)
	if os.name == 'posix':
		display.stop()
	return status

# Search an element in the web page
def search_element(driver, ElementID, timeout, StartTime):
	error = ''
	try:
		element = wait(driver, timeout).until(EC.presence_of_element_located((By.ID, ElementID)))
		availability = 1
	except:
		availability = 0
		error = 'Timeout in finding Element ID in the page'
	results = browser_perf(driver, StartTime, availability, error)
	return results
	
# Main function
def run_selenium(siteURL, authentication, username, password, ElementID, timeout, screenshot, logging):
	results = {}
	results['error'] = ''
	if logging:
		stopit_logger = logging.getLogger('stopit')
		stopit_logger.seLevel(logging.ERROR)
	with stopit.ThreadingTimeout(timeout) as to_ctx_mgr:
		assert to_ctx_mgr.state == to_ctx_mgr.EXECUTING
		# Chrome startup
		directory, driver, display = start_chrome_driver(authentication, username, password)		
		StartTime = int(round(time.time() * 1000))
		# navigation to the URL
		driver.get(siteURL)
		# Search element in page
		if ElementID:
			results = search_element(driver, ElementID, timeout, StartTime)
		else:
			results['availability'] = 0
			results['error'] = 'No Element ID defined'
	if to_ctx_mgr.state == to_ctx_mgr.TIMED_OUT:
		# Timeout occurred while executing the block
		results['availability'] = 0
		results['error'] = 'Timeout executing the test'
	elif to_ctx_mgr.state == to_ctx_mgr.EXECUTED:
		if screenshot:
			driver.save_screenshot('screenshot.png')
		# All's fine, everything was executed within timeout seconds
		# Close the browser
		if close_chrome_driver(driver, authentication, directory, display):
			results['error'] = results['error']
		else:
			results['error'] = results['error'] + ' Chrome driver not properly closed'
	return results

def run(test_config):
	config = json.loads(test_config)
	siteURL = config['siteURL']
	authentication = config['authentication']
	username = config['UserName']
	password = config['Password']
	ElementID = config['ElementID']
	timeout = config['Timeout']
	screenshot = config['Screenshot']
	logging = config['Logging']
	return json.dumps(run_selenium(siteURL, authentication, username, password, ElementID, timeout, screenshot, logging))

# Test configuration	
test_config = {
	'siteURL' : 'https://www.yahoo.com/news/politics/',
	'authentication' : False,
	'UserName' : '',
	'Password' : '',
	'ElementID' : 'YDC-Col2', # Yahoo
	'Timeout' : 30,
	'Screenshot' : True,
	'Logging' : False
}

results = run(json.dumps(test_config))
print(results) # we can verify on the nPoint this way