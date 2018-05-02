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
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.chrome.options import Options

'''
	Test: Launch a transaction in Omnitracker and return the availability, the connect time and the transaction time (including data loading time)
	Suggested Icon: open in browser
	Status: Development
	Description: This script launch an Omnitracker business transaction.
    Requirements:
		Chrome driver needs to be installed
	Logs:
    	
    Changes:
		v1:
			Linux platform compatibility
	Metrics:
        NAME            	UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        -------------------	----------- ----------- --------------------------- ----------- --------------------------------
        availability
        ot_dns				ms		    0                                       N           DNS query response time
		ot_ssl				ms			0										N			SSL Handshake response time
		ot_server			ms			0										N			Server + data network transfer time
		ot_client			ms			0										N			browser processing time
		ot_login			ms			0										N			overall transaction time
		ot_transaction		ms			0										N			Overall time for the page to be loaded and ready to use
		ot_network			ms			0										N			Network time
		
    Chart Settings:
        Y-Axis Title:   Response Time
        Chart Type:     Area
        Chart Stacking: Stacked (normal)

   Test Instance Template:
        NAME              			TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   	DESCRIPTION
        ------------------------	----------- ------- -------------------------- 	----------------------------------------------------------------------------------------------------------------
        SiteURL			  			text        100 			                	The complete URL of the StoreFront Receiver for Web site or NetScaler Gateway portal.
        UserName          			text        50                              	The name of the user which is used to log on. Acceptable forms are down-level logon name or user principal name.
        Password          			password    50                              	The password of the user which is used to log on.
		XPath						text		50									Element on the web page using XML path expression to find so that the web page is estimated to be loaded
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
	results['ot_login'] = performance['LoginTime']
	results['ot_transaction'] = performance['EndTime'] - performance['StartTime']
	results['ot_dns'] = performance['domainLookupEnd'] - performance['domainLookupStart']
	if (performance['secureConnectionStart'] == 0):
		results['ot_ssl'] = 0
	else:
		results['ot_ssl'] = performance['requestStart'] - performance['secureConnectionStart']
	results['ot_network'] = performance['connectEnd'] - performance['connectStart']
	results['ot_server'] = (performance['responseEnd'] - performance['navigationStart']) - results['ot_network']
	results['ot_client'] = performance['domComplete'] - performance['domLoading']
	#results['ot_transaction'] = performance['domComplete'] - performance['navigationStart']
	if (performance['loadEventStart'] == 0):
		results['ot_load_event'] = 0
	else:
		results['ot_load_event'] = performance['loadEventEnd'] - performance['loadEventStart']
	results['availability'] = availability
	results['error'] = error
	return results

# Retrieve the browser performance data
def browser_perf(self, start_time, login_time, availability, error):
	performance = {}
	performance['LoginTime'] = login_time
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
def start_chrome_driver(username, password):
	# Configure and start Chrome
	chrome_options = Options()
	# Use headless mode
	chrome_options.add_argument('no-sandbox')
	chrome_options.add_argument('start-maximized')
	# Authentication management
	directory = os.path.join('', str(uuid.uuid4()))
	if not os.path.exists(directory):
		os.makedirs(directory)
	if mgmt_authentication(directory, username, password):
		availability = 1
		extension = os.path.join(directory, 'background.zip')
		chrome_options.add_extension(extension)
		# OS dependant startup
		if os.name == 'nt':
			chrome_options.binary_location = CHROME_PATH
			display = ''
			driver = webdriver.Chrome(executable_path = CHROMEDRIVER_PATH, chrome_options = chrome_options)
		elif os.name == 'posix':
			display = Display(visible = 0, size = (1024, 768))
			display.start()
			chrome_options.add_argument("--verbose")
			chrome_options.add_argument('--disable-gpu')
			chrome_options.add_argument('--lang=en')
			driver = webdriver.Chrome(CHROME_PATH, chrome_options = chrome_options)
		else:
			availability = 0
			error = 'Error in authentication'
	else: # Not supported
		driver = ''	
	return directory, driver, display

# Exit Chrome driver
def close_chrome_driver(driver, directory, display):
	status = True
	driver.quit()
	shutil.rmtree(directory)
	if os.name == 'posix':
		display.stop()
	return status

# Search an element in the web page
def search_element(driver, XPath, timeout, StartTime, LoginTime):
	error = ''
	try:
		element = wait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, XPath)))
		availability = 1
	except:
		availability = 0
		error = 'Timeout in finding XPath in the page'
	results = browser_perf(driver, StartTime, LoginTime, availability, error)
	return results

# Check if a popup alert window is present when launching the URL
def is_alert_present(driver):
	try:
		driver.switch_to_alert()
	except NoAlertPresentException as e: return False
	return True

# Close the alert popup window and return text alert
def close_alert(driver):
	alert = driver.switch_to_alert()
	alert_text = alert.text
	alert.dismiss()
	return alert_text
	
# Main function
def run_selenium(siteURL, username, password, XPath, timeout, screenshot, logging):
	results = {}
	results['error'] = ''
	if logging:
		stopit_logger = logging.getLogger('stopit')
		stopit_logger.seLevel(logging.ERROR)
	with stopit.ThreadingTimeout(timeout) as to_ctx_mgr:
		assert to_ctx_mgr.state == to_ctx_mgr.EXECUTING
		# Chrome startup
		directory, driver, display = start_chrome_driver(username, password)		
		LoginStartTime = int(round(time.time() * 1000))
		# navigation to the URL
		driver.get(siteURL)
		if is_alert_present(driver):
			alert_text = close_alert(driver)
		# Omnitracker login page management
		driver.find_element_by_id("UsernameInput").clear()
		driver.find_element_by_id("UsernameInput").send_keys(username)
		driver.find_element_by_id("PasswordInput").clear()
		driver.find_element_by_id("PasswordInput").send_keys(password)
		driver.find_element_by_id("LoginButton").click()
		LoginStopTime = int(round(time.time() * 1000))
		LoginTime = LoginStopTime - LoginStartTime
		# Search element in page
		TransactionStartTime = int(round(time.time() * 1000))
		if XPath:
			results = search_element(driver, XPath, timeout, TransactionStartTime, LoginTime)
		else:
			results['availability'] = 0
			results['error'] = 'No Element ID defined'
	if to_ctx_mgr.state == to_ctx_mgr.TIMED_OUT:
		# Timeout occurred while executing the block
		results['availability'] = 0
		results['error'] = 'Timeout executing the test'
	elif to_ctx_mgr.state == to_ctx_mgr.EXECUTED:
		if screenshot:
			driver.save_screenshot('omnitracker.png')
		# All's fine, everything was executed within timeout seconds
		# Close the browser
		if close_chrome_driver(driver, directory, display):
			results['error'] = results['error']
		else:
			results['error'] = results['error'] + ' Chrome driver not properly closed'
	return results

def run(test_config):
	config = json.loads(test_config)
	siteURL = config['siteURL']
	username = config['UserName']
	password = config['Password']
	XPath = config['XPath']
	timeout = config['Timeout']
	screenshot = config['Screenshot']
	logging = config['Logging']
	return json.dumps(run_selenium(siteURL, username, password, XPath, timeout, screenshot, logging))

# Test configuration	
test_config = { 
	'siteURL' : 'https://omnitracker.test.com/otwg/?tzo=-120',
	'UserName' : 'login',
	'Password' : 'passwd',
	'XPath' : '/html/body/form/div[4]/div/div[3]/main/div/div[2]/div/div/div/table/tbody/tr[1]/td[2]',  
	'Timeout' : 30,
	'Screenshot' : True,
	'Logging' : False
}

#results = run(json.dumps(test_config))
#print(results) # we can verify on the nPoint this way