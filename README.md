# DRTM-Backend
DMR RealTime Monitor backend

* create_db.py: Script for creating the database needed
* pytrap.py: Daemon for receiving the traps from the Hytera repeaters
* pyget.py: Daemon for polling the rssi data from the Hytera repeaters
* pydmruser.py: Daemon for polling the user and talkgroup data from the master in Germany
* update_db.py: Script for polling repeater data from the webinterface

# Install
This guide expects you are running Debian 8 or one of the last versions of Ubuntu
```
pip install paho-mqtt
pip install pysnmp
apt-get install snmp python-sqlite
cp dmr.conf_example dmr.conf
python create_db.py
```
* Edit the dmr.conf
* Now you should be able to start the daemons
* Create a cronjob to run update_db.py every 15m to update the repeaters from the webinterface.

NOTE: This is still incomplete!!!
