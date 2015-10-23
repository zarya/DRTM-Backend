import urllib2
import json
import ConfigParser
import sqlite3
import sys
import os
import logging

def getPage(url):
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    return response.read() 

config = ConfigParser.RawConfigParser()
config.read('%s/dmr.conf' % ( os.path.dirname(os.path.abspath(__file__)) ))

#loggin stuff
logging.basicConfig(filename=config.get('Logging','file'), level=int(config.get('UpdateDB','loglevel')))
logger = logging.getLogger("UpdateDB")

#catch exceptions and write them to the logfile
def my_excepthook(excType, excValue, traceback, logger=logger):
    logger.error("Logging an uncaught exception",
                 exc_info=(excType, excValue, traceback))

sys.excepthook = my_excepthook


repeaters = json.loads(getPage(config.get("Webapi","url")))

con = sqlite3.connect(config.get('DB','path'))
cur = con.cursor() 

for repeater,data in repeaters.iteritems():
    logger.debug("%s %s" % ( repeater,data['ip'] ))
    if data['rssi'] == 0:
        snmp = 0
    else:
        snmp = 1
 
    cur.executescript("""
        INSERT OR REPLACE INTO repeaters (Call, IP, SNMP, RID) 
        VALUES ('%s', '%s', %s, %s);
    """ % (repeater,data['ip'],snmp,data['id']))
try:
    con.commit()
except sqlite3.Error, e:
    
    if con:
        con.rollback()
        
    logger.error("Error %s:" % e.args[0])
    sys.exit(1)
