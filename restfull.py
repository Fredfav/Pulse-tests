import json
import pycurl
import StringIO

def run(testConfig):
	configuration = json.loads(testConfig)
	url = configuration['url']
	http_header = configuration['http_header']
	post_fields = configuration['post_fields']
	
	return json.dumps(restAPI(url, http_header, post_fields))
	
def restAPI(url, http_header, post_fields):
	results = {}
	results['error'] = 0
	results['response_time'] = 0.0
	results['availability'] =0 
	
	response = StringIO.StringIO()
	c = pycurl.Curl()
	#c.setopt(c.URL, url)
	c.setopt(c.URL, 'http://10.10.10.3:8080/dbonequerydata/?username=administrator/password=netscout1/encrypted=false/conversion=true/DT=csv -o /root/output.csv')
	c.setopt(c.WRITEFUNCTION, response.write)
	#c.setopt(c.HTTPHEADER, [http_header])
	c.setopt(c.HTTPHEADER, ['Content-Type: text/xml', 'charset=UTF-8'])
	#c.setopt(c.POSTFIELDS, post_fields)
	c.setopt(c.POSTFIELDS, "@/root/session.xml")
	c.perform()
	results['error'] = c.getinfo(c.RESPONSE_CODE)
	results['response_time'] = c.getinfo(c.TOTAL_TIME)
	results['availability'] = true
	c.close()
	
	return results