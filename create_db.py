import sqlite3
import sys

con = sqlite3.connect('repeater.db') 
try:
    cur = con.cursor()    
    cur.executescript("""
DROP TABLE IF EXISTS repeaters; 
CREATE TABLE repeaters(Id INTEGER PRIMARY KEY, Call TEXT UNIQUE, IP TEXT, SNMP INTEGER, RID INTEGER);
    """)
    con.commit()       
except sqlite3.Error, e:
    
    if con:
        con.rollback()
        
    print "Error %s:" % e.args[0]
    sys.exit(1)
print("Database created"); 
