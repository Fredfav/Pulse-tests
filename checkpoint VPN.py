from subprocess import check_output
from os import path
import time
import json
import random
import requests

'''
    Test: Web Test through a Checkpoint VPN
    Suggested Icon: rss_feed
    Status: Production
    Description:
        Web Test that allows the Checkpoint VPN credentials to be specified 

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        res_time        seconds     3           --                          N           Response Time
		dns_time        seconds     3           --                          N           DNS Time
		net_time        seconds     3           --                          N           Network Time
		ssl_time        seconds     3           --                          N           SSL Time
		cli_time        seconds     3           --                          N           Client Time
		app_time        seconds     3           --                          N           Application Server Time
		svr_time        seconds     3           --                          N           Server Time

    Chart Settings:
        Y-Axis Title:   Response Time
        Chart Type:     Area
        Chart Stacking: Stacked (normal)

   Test Instance Template:
        NAME            TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        --------------- ----------- ------- ----------------------- ---------------------------------------------------
        url             text        100                             URL to test to
		vpn			    text        100                             The CheckPoint VPN Server the Web Test should go through
		port			text		10								The CheckPoint VPN server port 
		username        text        100                             The username for the VPN Server
		password        text        100                             The password for the VPN Server
'''

format = ('{'
  '"time_namelookup": %{time_namelookup},'
  '"time_connect": %{time_connect},'
  '"time_appconnect": %{time_appconnect},'
  '"time_pretransfer": %{time_pretransfer},'
  '"time_redirect": %{time_redirect},'
  '"time_starttransfer": %{time_starttransfer},'
  '"time_total": %{time_total}'
'}')

format_file = "curl-format.txt"

############################## INPUT ############################## 
DOMAIN = "url"
VPN_DOMAIN = "vpn"
VPN_PORT = "port"
VPN_USR = "username"
VPN_PASS = "password"

############################## OUTPUT #############################
DNS_TIME = "dns_time"
NETWORK_TIME = "network_time"
SSL_TIME = "ssl_time"
CLIENT_TIME = "client_time"
APP_TIME = "app_time"
SERVER_TIME = "server_time"
RSP_TIME = "total_time"
###################################################################

class Config(object):
    def __init__(self, config):
        self.domain = config[DOMAIN]
        if VPN_DOMAIN in config and config[VPN_DOMAIN] is not None and config[VPN_DOMAIN] != '':
            self.vpn = True
            self.vpn_domain = config[VPN_DOMAIN]
			self.vpn_port = config[VPN_PORT]
            self.vpn_username = config[VPN_USR]
            self.vpn_password = config[VPN_PASS]
        else:
            self.vpn = False

	def __api_call__(ip_addr, port, command, json_payload, sid):
		url = 'https://' + self.vpn_domain + ':' + self.vpn_port + '/web_api/' + command
		if sid == '':
			request_headers = {'Content-Type' : 'application/json'}
		else:
			request_headers = {'Content-Type' : 'application/json', 'X-chkp-sid' : sid}
		r = requests.post(url,data=json.dumps(json_payload), headers=request_headers)
		return r.json()

	# Log in to the server with username and password.
	# The server shows your session unique identifier. Enter this session unique identifier in the 'X-chkp-sid' header of each request.
	def __login__(user, password):
		payload = {'user':self.vpn_user, 'password' : self.vpn_password}
		response = self.__api_call__(self.vpn_domain, 443, 'login',payload, '')
		return response["sid"]

	def __logout__(self):
		return self.__api_call__(self.vpn_domain, 443,"logout", {},sid)
			
    def __str__(self):
        ret = ''
        ret = 'curl -L --max-redirs 5 -w "@' + format_file + '" -o /dev/null -s ' + self.domain
        return ret

class Result(object):
    def __init__(self, data):
        self.dnsTime = data['time_namelookup']
        self.connectTime = data['time_connect']
        self.preTransferTime = data['time_pretransfer']
        self.startTransferTime = data['time_starttransfer']
        self.appConnectTime = data['time_appconnect']
        self.totalTime = data['time_total']
        
        self.SSLTime = 0
        self.networkRoundTrip = self.connectTime - self.dnsTime
        self.transferTime = self.startTransferTime - self.preTransferTime

        if self.networkRoundTrip < self.transferTime:
            self.appDelay = self.transferTime - self.networkRoundTrip
            self.networkRoundTripTrim = 0
        else:
            if self.networkRoundTrip <= 1.5 * self.transferTime:
                self.appDelay = self.networkRoundTrip - self.transferTime
            else:
                self.appDelay = 0.25 * self.transferTime
            self.networkRoundTripTrim = self.networkRoundTrip - (self.transferTime - self.appDelay)
            self.networkRoundTrip = self.transferTime - self.appDelay

        self.clientDelay = self.preTransferTime - self.connectTime
        self.serverDelay = self.totalTime - self.startTransferTime

        if self.appConnectTime > 0:
            self.SSLTime = self.appConnectTime - self.connectTime
            self.clientDelay -= self.SSLTime
            if self.clientDelay < 0:
                self.clientDelay = 0

        self.clientDelay += 0.5 * self.networkRoundTrip
        self.serverDelay += 0.5 * self.networkRoundTrip

        self.serverDelay += self.networkRoundTripTrim

    def toJson(self):
        ret = { 'availability': 1 }
        ret[DNS_TIME] = self.dnsTime
        ret[NETWORK_TIME] = self.networkRoundTrip
        ret[SSL_TIME] = self.SSLTime
        ret[CLIENT_TIME] = self.clientDelay
        ret[APP_TIME]  = self.appDelay
        ret[SERVER_TIME] = self.serverDelay
        ret[RSP_TIME] = self.totalTime

        return json.dumps(ret)


def run_curl(config):
    command = str(config)
    output = ''
    max_retry = 5
    i = 0
    while i < max_retry:
        try:
            output = check_output(command, shell=True)
            output = json.loads(output)
            break
        except:
            output = 'failed'
            i += 1
        print output
        if output == 'failed':
            time.sleep(random.randint(1,5))
        else:
            break
    return i < max_retry, output


def calculate(config):
    success, raw_output = run_curl(config)
    if not success:
        return json.dumps({'availability': 0})
    rst = Result(raw_output)
    return rst.toJson()

    
def run(test_config):
    config = json.loads(test_config)
    # print config
    if(not path.isfile(format_file)) :
        with open(format_file, 'w') as f:
            f.write(format)
    config = Config(config)
    # print config
    ret = calculate(config)
    # print ret
    return ret 

# test_config = {
#     'url' : 'http://www.google.com/',
#     'vpn' : '192.0.2.1',
#     'port' : '443',
#     'username' : 'aa',
#     'password' : 'aaaa'
# }
# run(json.dumps(test_config))
