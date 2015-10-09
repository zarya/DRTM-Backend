from struct import unpack
import paho.mqtt.publish as publish
import subprocess 
import sqlite3
import ConfigParser
import logging
import sys
from daemon import Daemon
import logging
import time
import os

config = ConfigParser.RawConfigParser()
config.read('%s/dmr.conf' % ( os.path.dirname(os.path.abspath(__file__)) ))

mqtt_host = config.get("MQTT","host")

#Logging
logging.basicConfig(filename=config.get('Logging','file'), level=int(config.get('Getter','loglevel')))
logger = logging.getLogger("Getter")

def my_excepthook(excType, excValue, traceback, logger=logger):
    logger.error("Logging an uncaught exception",
                 exc_info=(excType, excValue, traceback))

sys.excepthook = my_excepthook  

def dataparse(client,ent,value):
    var_type = ""
    if ent == "1.3.6.1.4.1.40297.1.2.1.2.9.0":
        ent = "rptSlot1Rssi"
        var_type = "int" 

    elif ent == "1.3.6.1.4.1.40297.1.2.1.2.10.0":
        ent = "rptSlot2Rssi"
        var_type = "int" 
    
    logger.debug("%s-%s-(%s)=%s" % (client,ent,var_type,value))
    if var_type == "float":
        publish.single("hytera/%s/%s" % (client, ent) , unpack('f',str(value))[0], hostname=mqtt_host)
    elif var_type == "int":
        publish.single("hytera/%s/%s" % (client, ent) , int(value), hostname=mqtt_host)
    elif var_type == "alarm":
        if int(value) == -1:
            publish.single("hytera/%s/%s" % (client, ent) , 'Undefined', hostname=mqtt_host)
        elif int(value) == 0:
            publish.single("hytera/%s/%s" % (client, ent) , 'Normal', hostname=mqtt_host)
        elif int(value) == 1:
            publish.single("hytera/%s/%s" % (client, ent) , 'Alarm', hostname=mqtt_host)

    elif var_type == "workstate":
        if int(value) == 0:
            publish.single("hytera/%s/%s" % (client, ent) , 'Receive', hostname=mqtt_host)
        elif int(value) == 1:
            publish.single("hytera/%s/%s" % (client, ent) , 'Transmit', hostname=mqtt_host)
    else:
        logger.debug(ent)

class Getter(Daemon):
    def run(self):
        while True:
            try:
                con = sqlite3.connect(config.get('DB','path'))
                cur = con.cursor()
                cur.execute("SELECT * FROM repeaters WHERE SNMP=1")
                rows = cur.fetchall()
            except:
                logger.error("DB error")
                time.sleep(float(config.get("Getter","sleeptime")))

            for row in rows:
                host = row[2]
                output = subprocess.Popen("snmpget -t 2 -r 0 -On -v1 -c public %s 1.3.6.1.4.1.40297.1.2.1.2.9.0" % host, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
                output = output.split(" ")
                if len(output) > 2:
                    oid = output[0][1:]
                    value = output[3]
                    dataparse(host,oid,value)
                    output = subprocess.Popen("snmpget -t 2 -r 0 -On -v1 -c public %s 1.3.6.1.4.1.40297.1.2.1.2.10.0" % host, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
                    output = output.split(" ")
                    try:
                        oid = output[0][1:]
                        value = output[3]
                        dataparse(host,oid,value)
                    except:
                        logger.error("Value missing for %s" % (host))
                        continue
                else:
                    publish.single("hytera/%s/%s" % (host, "rptVoltageAlarm") , 'Alarm', hostname=mqtt_host)
                    publish.single("hytera/%s/%s" % (host, "rptTemperatureAlarm") , 'Alarm', hostname=mqtt_host)
                    publish.single("hytera/%s/%s" % (host, "rptSlot1Rssi") , 'DOWN', hostname=mqtt_host)
                    publish.single("hytera/%s/%s" % (host, "rptSlot2Rssi") , 'DOWN', hostname=mqtt_host)
                    publish.single("hytera/%s/%s" % (host, "rptVoltage") , 0, hostname=mqtt_host)
                    publish.single("hytera/%s/%s" % (host, "rptPaTemprature") , 0, hostname=mqtt_host)
                    publish.single("hytera/%s/%s" % (host, "rptVswr") , 0, hostname=mqtt_host)
                    publish.single("hytera/%s/%s" % (host, "rptTxFwdPower") , 0, hostname=mqtt_host)
                    publish.single("hytera/%s/%s" % (host, "rptTxRefPower") , 0, hostname=mqtt_host)
            time.sleep(float(config.get("Getter","sleeptime")))


if __name__ == "__main__":
    daemon = Getter('/var/run/rtm_getter.pid')
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
