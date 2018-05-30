from pysnmp.hlapi import *
from pysnmp.smi import builder, view, error, rfc1902
import json

'''
	Test: Custom SNMP polling
	Suggested Icon: poll
	Status: Development
	Description: The purpose of this test is to be able to fetch scalar variables. This script perform similar to snmpget command
    Requirements:
		pySNMP needs to be installed
	Logs:
    	
    Changes:
		v1:
			Initial version
	Metrics:
        NAME            	UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        -------------------	----------- ----------- --------------------------- ----------- --------------------------------
        availability
		scalar				ms			0										N			Scalar data
		
    Chart Settings:
        Y-Axis Title:   Value
        Chart Type:     Line
        Chart Stacking: Stacked (normal)

   Test Instance Template:
        NAME              			TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   	DESCRIPTION
        ------------------------	----------- ------- -------------------------- 	----------------------------------------------------------------------------------------------------------------
        community			  		text        50 			                		SNMP community string
		version						list											SNMP version v1, v2 or v3
		server						text		50									Server name or IP to poll
		port						integer		161									SNMP port (to feed if different of the default one)
		OID							text		200									OID to poll
		auth_method					list											Authentication method for SNMPv3 (usr-md5-des, usr-md5-none, usr-none-none, usr-sha-aes)
		authkey						text		200									Authentication key for SNMPv3 authentication
		privkey						text		200									Private key for SNMPv3 authentication
		authProtocol				list		50									Authentication protocol for SNMPv3 SHA AES (usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol, usmHMAC128SHA224AuthProtocol,
																					usmHMAC192SHA256AuthProtocol, usmHMAC256SHA384AuthProtocol, usmHMAC384SHA512AuthProtocol, usmNoAuthProtocol)
		privProtocol				list		50									Privacy protocol for SNMPv3 authentication SHA AES (usmDESPrivProtocol, usm3DESEDEPrivProtocol, usmAesCfb128Protocol,
																					usmAesCfb192Protocol, usmAesCfb256Protocol, usmNoPrivProtocol)
'''

###################################################################
# Splitting up functions for better error reporting potential
# MIB compilation and retrieval
def initialize(MIB, var, index):
	# MIB Builder manages pysnmp MIBs
	mibBuilder = builder.MibBuilder()
	# MIB View Controller implements various queries to loaded MIBs
	mibView = view.MibViewController(mibBuilder)
	# Obtain MIB object information by MIB object name
	mibVar = rfc1902.ObjectIdentity(MIB, var, int(index))
	# Attach PySMI MIB compiler to MIB Builder that would create pysnmp MIBs on demand from ASN.1 sources downloaded from a web site
	try:
		mibVar.addAsn1MibSource('http://mibs.snmplabs.com/asn1/@mib@')
	except error.SmiError:
		print('WARNING: not using MIB compiler (PySMI not installed)')
	mibVar.resolveWithMib(mibView)
	return True
	
# Split the OID into object identity
def split_OID(OID):
	s = OID.split('::')
	MIB = s[0]
	s = s[1].split('.')
	var = s[0]
	index = s[1]
	return MIB, var, index
	
# SNMP get v1 / v2 function
def snmp_get_v1(community, version, server, port, OID):
	MIB, var, index = split_OID(OID)
	initialize(MIB, var, index)
	g = getCmd(SnmpEngine(), CommunityData(community), UdpTransportTarget((server, port)), ContextData(), ObjectType(ObjectIdentity(MIB, var, int(index))))
	errorIndication, errorStatus, errorIndex, varBinds = next(g)
	return errorIndication, errorStatus, errorIndex, varBinds

# SNMP get v3 function
def snmp_get_v3(server, port, OID, auth_method, authkey, privkey, auth_protocol, priv_protocol):
	MIB, var, index = split_OID(OID)
	initialize(MIB, var, index)
	if auth_method == 'usr-md5-des':
		g = getCmd(SnmpEngine(), UsmUserData(auth_method, authkey, privkey), UdpTransportTarget((server, port)), ContextData(), ObjectType(ObjectIdentity(MIB, var, int(index))))
	elif auth_method == ' usr-md5-none':
		g = getCmd(SnmpEngine(), UsmUserData(auth_method, authkey), UdpTransportTarget((server, port)), ContextData(), ObjectType(ObjectIdentity(MIB, var, int(index))))
	elif auth_method == 'usr-none-none':
		g = getCmd(SnmpEngine(), UsmUserData(auth_method), UdpTransportTarget((server, port)), ContextData(), ObjectType(ObjectIdentity(MIB, var, int(index))))
	else: # auth_method == 'usr-sha-aes'
		g = getCmd(SnmpEngine(), UsmUserData(auth_method, authkey, privkey, auth_protocol, priv_protocol), UdpTransportTarget((server, port)), ContextData(), ObjectType(ObjectIdentity(MIB, var, int(index))))
	errorIndication, errorStatus, errorIndex, varBinds = next(g)
	return errorIndication, errorStatus, errorIndex, varBinds
	
# Query the SNMP OID
def query_oid(community, version, server, port, OID, auth_method, authkey, privkey, auth_protocol, priv_protocol):
	# initialization
	results = {}
	# SNMP queries
	if version == 'v1':
		errorIndication, errorStatus, errorIndex, varBinds = snmp_get_v1(community, version, server, port, OID)
	if version == 'v2':
		errorIndication, errorStatus, errorIndex, varBinds = snmp_get_v1(community, version, server, port, OID)
	if version == 'v3':
		errorIndication, errorStatus, errorIndex, varBinds = snmp_get_v1(server, port, OID, auth_method, authkey, privkey, auth_protocol, priv_protocol)
	if errorIndication: # SNMP engine error
		results['availability'] = 0
		results['error'] = errorIndication
	else:
		if errorStatus: # SNMP agent error
			results['availability'] = 0
			results['error'] = '%s at %s' % (errorStatus.prettyPrint(), varBinds[int(errorIndex)-1] if errorIndex else '?')
		else:
			results['availability'] = 1
			results['error'] = ''
			name, value = varBinds[0]
			result = int(value.prettyPrint())
			print type(result)
			print result
			results['scalar'] = result
	return results

def run(test_config):
	config = json.loads(test_config)
	community = config['community']
	version = config['version']
	server = config['server']
	port = config['port']
	OID = config['OID']
	auth_method = config['auth_method']
	authkey = config['authkey']
	privkey = config['privkey']
	auth_protocol = config['authProtocol']
	priv_protocol = config['privProtocol']
	return json.dumps(query_oid(community, version, server, port, OID, auth_method, authkey, privkey, auth_protocol, priv_protocol))

# Test configuration	
test_config = {
	'community' : 'public',
	'version' : 'v1',
	'server' : 'demo.snmplabs.com',
	'port' : 161,
	'OID' : 'IF-MIB::ifInOctets.1',
	'auth_method' : 'usr-md5-des', # usr-md5-des, usr-md5-none, usr-none-none, usr-sha-aes
	'authkey' : 'authkey1',
	'privkey' : 'privkey1',
	'authProtocol' : 'usmHMACMD5AuthProtocol', # usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol, usmHMAC128SHA224AuthProtocol, usmHMAC192SHA256AuthProtocol, usmHMAC256SHA384AuthProtocol, usmHMAC384SHA512AuthProtocol, usmNoAuthProtocol
	'privProtocol' : 'usmDESPrivProtocol' # usmDESPrivProtocol, usm3DESEDEPrivProtocol, usmAesCfb128Protocol, usmAesCfb192Protocol, usmAesCfb256Protocol, usmNoPrivProtocol
}

results = run(json.dumps(test_config))
print(results) # we can verify on the nPoint this way