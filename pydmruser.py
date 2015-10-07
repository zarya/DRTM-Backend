from struct import unpack
from time import sleep
from dateutil.parser import parse as dtparse
from dateutil import tz
from daemon import Daemon
import paho.mqtt.publish as publish
import subprocess 
import urllib2
import re
import datetime
import sqlite3
import ConfigParser
import os
import sys
import logging

config = ConfigParser.RawConfigParser()
config.read('%s/dmr.conf' % ( os.path.dirname(os.path.abspath(__file__)) ))

mqtt_host = config.get("MQTT","host")

con = sqlite3.connect(config.get('DB','path'))

fieldwidths = [14, 15, 8, 8, 9, 8, 10, 23, 20, 5, 21, 20]

#loggin stuff
logging.basicConfig(filename=config.get('Logging','file'), level=int(config.get('Users','loglevel')))
logger = logging.getLogger("DMRUser")
logger.debug("pre init")

#catch exceptions and write them to the logfile
def my_excepthook(excType, excValue, traceback, logger=logger):
    logger.error("Logging an uncaught exception",
                 exc_info=(excType, excValue, traceback))

sys.excepthook = my_excepthook

 
def getPage():
    url="http://ham-dmr.de/live_dmr/jj3.yaws"
 
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    return response.read()


tsLog = [{},{}] 

def parse(data,fields):
    outputList = []
    for line in data.split("\n"):
        idx = 0
        lineList = []
        for i in fieldwidths:
            upper = idx+i
            cell = line[idx:upper]
            cell = cell.replace('_','')
            lineList.append(cell)
            idx = upper
        outputList.append(lineList)
    return outputList

class UGetter(Daemon):
    def run(self):
        logger.debug("Starting")
        while True:
            lines = parse(getPage(),fieldwidths)
            for line in lines:
                #bla query
                cur = con.cursor()    
                cur.execute("""SELECT * FROM repeaters WHERE Call = "%s"; """ % (line[3].lower()))
                data = cur.fetchone()

                if isinstance(data, (list, tuple)):
                    if re.match('[a-zA-Z0-9_]',line[2]):
                        try:
                            logging.debug("%s TS%s: %s (%s) at %s:%s %s-%s-%s on %s" % (line[3],int(line[6]),line[2],line[8][1:],line[0][10:12],line[0][8:10],line[0][6:8],line[0][4:6],line[0][0:4],line[7][2:]))
                        except:
                            logging.debug("Line error")
                            continue
                        value = "%s (%s)" % (line[2],line[8][1:])
                        publish.single("hytera/%s/usrTs%s" % (data[2], int(line[6])) , value, hostname=mqtt_host)
                        publish.single("hytera/%s/tlkTs%s" % (data[2], int(line[6])) , line[7][2:], hostname=mqtt_host)
                        dt=dtparse("%s UTC"%line[0])
                        try:
                            dt = dt.astimezone(tz.tzlocal())
                            tsLog[int(line[6])-1][data[2]] = dt.strftime("%s")
                        except:
                            logger.error("astimezone broke")

            for key,value in tsLog[0].iteritems():
                publish.single("hytera/%s/lastTs1" % (key), value, hostname=mqtt_host)

            for key,value in tsLog[1].iteritems():
                publish.single("hytera/%s/lastTs2" % (key), value, hostname=mqtt_host)
                
            sleep(float(config.get("Users","sleeptime")))

if __name__ == "__main__":
    logger.debug("Init")
    daemon = UGetter('/var/run/rtm_user.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)

