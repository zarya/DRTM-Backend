import ConfigParser
import paho.mqtt.publish as publish
import logging
import time
import sys
import os
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from struct import unpack
from daemon import Daemon

config = ConfigParser.RawConfigParser()
config.read('%s/dmr.conf' % ( os.path.dirname(os.path.abspath(__file__)) ))

#loggin stuff
logging.basicConfig(filename=config.get('Logging','file'), level=int(config.get('Trapper','loglevel')))
logger = logging.getLogger("Trapper")

#catch exceptions and write them to the logfile
def my_excepthook(excType, excValue, traceback, logger=logger):
    logger.error("Logging an uncaught exception",
                 exc_info=(excType, excValue, traceback))

sys.excepthook = my_excepthook

mqtt_host = config.get("MQTT","host")

def cbFun(transportDispatcher, transportDomain, transportAddress, wholeMsg):
    while wholeMsg:
        msgVer = int(api.decodeMessageVersion(wholeMsg))
        if msgVer in api.protoModules:
            pMod = api.protoModules[msgVer]
        else:
            logger.error('Unsupported SNMP version %s' % msgVer)
            return
        reqMsg, wholeMsg = decoder.decode(
            wholeMsg, asn1Spec=pMod.Message(),
            )
        reqPDU = pMod.apiMessage.getPDU(reqMsg)
        if reqPDU.isSameTypeWith(pMod.TrapPDU()):
            ent = pMod.apiTrapPDU.getEnterprise(reqPDU).prettyPrint()
            varBinds = pMod.apiTrapPDU.getVarBindList(reqPDU)
            var_type = ""
            if ent == "1.3.6.1.4.1.40297.1.2.1.2.1.0":
                ent = "rptVoltage"
                var_type = "float"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.2.0":
                ent = "rptPaTemprature"
                var_type = "float"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.3.0":
                ent = "rptFanSpeed"
                var_type = "int"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.4.0":
                ent = "rptVswr"
                var_type = "float" 

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.5.0":
                ent = 'rptTxFwdPower'
                var_type = "float" 

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.6.0":
                ent = "rptTxRefPower"
                var_type = "float" 

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.7.0":
                ent = "rptDataInfoBak1"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.8.0":
                ent = "rptDataInfoBak2"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.9.0":
                ent = "rptSlot1Rssi"
                var_type = "int" 

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.10.0":
                ent = "rptSlot2Rssi"
                var_type = "int" 

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.11.0":
                ent = "rptSupplyPowerType"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.12.0":
                ent = "rptBatteryConnect"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.2.13.0":
                ent = "rptBatteryVoltage"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.1.1.0":
                ent = "rptVoltageAlarm"
                var_type = "alarm"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.1.2.0":
                ent = "rptTemperatureAlarm"
                var_type = "alarm"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.1.3.0":
                ent = "rptFanAlarm"
                var_type = "alarm"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.1.4.0":
                ent = "rptForwardAlarm"
                var_type = "alarm"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.1.5.0":
                ent = "rptReflectedAlarm"
                var_type = "alarm"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.1.6.0":
                ent = "rptVswrAlarm"
                var_type = "alarm"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.1.7.0":
                ent = "rptTxPllAlarm"
                var_type = "alarm"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.1.8.0":
                ent = "rptRxPllAlarm"
                var_type = "alarm"

            elif ent == "1.3.6.1.4.1.40297.1.2.1.1.9.0":
                ent = "rptBatteryVoltageAlarm"
                var_type = "alarm"

            elif ent == "1.3.6.1.4.1.40297.1.2.4.12.0":
                ent = "rptWorkState"
                var_type = "workstate"
            
            value = pMod.apiVarBind.getOIDVal(varBinds[0])[1]
            client = transportAddress[0]
            logger.debug("%s %s (%s)" % (client,ent,var_type))
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
                print ent
    return wholeMsg

class Trapper(Daemon):
    def run(self):
        transportDispatcher = AsynsockDispatcher()
        transportDispatcher.registerRecvCbFun(cbFun)
        # UDP/IPv4
        transportDispatcher.registerTransport(
            udp.domainName, udp.UdpSocketTransport().openServerMode(('0.0.0.0', 162))
        )

        transportDispatcher.jobStarted(1)

        try:
            # Dispatcher will never finish as job#1 never reaches zero
            transportDispatcher.runDispatcher()
        except:
            transportDispatcher.closeDispatcher()
            raise

if __name__ == "__main__":
    daemon = Trapper('/var/run/rtm_trapper.pid')
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
