import urllib2
import json
import ConfigParser
import sqlite3
import sys

def getPage(url):
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    return response.read() 

config = ConfigParser.RawConfigParser()
config.read('dmr.conf')

repeaters = json.loads(getPage(config.get("Webapi","url")))

con = sqlite3.connect('repeater.db')
cur = con.cursor() 

for repeater,data in repeaters.iteritems():
    print repeater
    print data['ip']
    if data['rssi'] == 0:
        snmp = 0
    else:
        snmp = 1
 
    cur.executescript("""
        INSERT OR REPLACE INTO repeaters (Call, IP, SNMP) 
        VALUES ('%s', '%s', %s);
    """ % (repeater,data['ip'],snmp))
try:
    con.commit()
except sqlite3.Error, e:
    
    if con:
        con.rollback()
        
    print "Error %s:" % e.args[0]
    sys.exit(1)
