'''
    Test: Postgresql
    Suggested Icon: kitchen
    Description: 
        This test makes a simple query to a postsql database
        This test returns the time it takes to connect to the database as well as the duration taken by the query

	NOTE: this test can only be run on a Virtual Pulse, where the psycopg2 module is installed

    Metrics:
        NAME            UNITS       DECIMALS    MIN/DEGRADED/CRITICAL/MAX   INVERTED    DESCRIPTION
        --------------- ----------- ----------- --------------------------- ----------- --------------------------------
        connect_time    ms 	    2                                                   How long does it take to connect to postgresql
        query_time      ms          2           0/100/500/99999                         Time taken by the query

    Chart Settings:
        Y-Axis Title:   DB perfromance
        Chart Type:     Area
        Chart Stacking: Stacking (normal)

    Test Instance Template:
        NAME            TYPE        SIZE    DEFAULT/MIN/MAX/UNITS   DESCRIPTION
        --------------- ----------- ------- ----------------------- ---------------------------------------------------
        server          text        50                              server hosting the DB
        username        text        50                              username allowed to connect and execute the query
        password        text   	    50	                            password
        dbname          text        50                              name of the DB
	query           text	    256			            query to execute
'''
import json
import psycopg2
import time


def pg_connect(server, dbname, username, password):
    return psycopg2.connect("dbname='" + dbname + "' user='"+ username + "' host='" + server + "' password='" + password + "'")


def get_row_count(conn, query):
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    return str(len(rows))


def driver(server, dbname, username, password, query):
    result= { 'availability': 0, 'connect_time': 0, 'query_time': 0, 'row_count': 0}
    start_time = time.time()
    conn = pg_connect(server, dbname, username, password)
    connect_time = time.time()
    result['connect_time'] = 100 * (connect_time - start_time)
    result['row_count'] = get_row_count(conn, query)
    result['query_time'] = 100 * (time.time() - connect_time)
    result['availability'] = 1
    return result


def run(test_config):
    config = json.loads(test_config)
    return json.dumps(driver(config['server'], config['dbname'], config['username'], config['password'], config['query']))
