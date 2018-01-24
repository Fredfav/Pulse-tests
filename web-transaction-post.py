# web-transaction-get.py
# this HW pulse script a web transaction GET.
# the arguments are : None
# 
# default values
# url: https://andruxnet-random-famous-quotes.p.mashape.com
# cat: famous
# number: 10

import json
import unirest
import time
 
def run(testConfig):
	configuration = json.loads(testConfig)
	url = configuration['url']
	cat = configuration['category']
	number = configuration['count']
	response_code = configuration['response_code']
	response_body = configuration['response_body']
	
	return json.dumps(web_transaction_get(url, key, category, count, response_code, response_body))
	
def web_transaction_get(url, key):
	results = {'error_code': null, 'response_time': null, 'availability': false}

	start_time = time.time()
	
	response = unirest.post(url, 
		headers = {"X-Mashape-Key": "zNBOE1gY95mshrP8TkNpwY4sNMuLp1PQflUjsnm6u6acIk2rZQ", "Accept": "application/json"}, 
		params = {"cat": cat, "count": number}
	)
	
	interval = time.time() - start_time
	
	if passing:
		results['error_code'] = response.code
		results['availability'] = true
		results['response_time'] = interval
	
	return results