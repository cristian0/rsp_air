import time
import sqlite3
from PiicoDev_ENS160 import PiicoDev_ENS160 # import the device driver
from pathlib import Path
import sys

def insert_sampling(aqi, tvoc, eco2, mode):

    con = sqlite3.connect(Path(__file__).resolve().parent / "air.db")
    cur = con.cursor()

    res = cur.execute("SELECT name FROM sqlite_master")
    if res.fetchone() is None:
        cur.execute("CREATE TABLE air (date INT, aqi INT, tvoc INT, eco2 INT, mode )")

    now = int(time.time())

    cur.execute("INSERT INTO air (date, aqi, tvoc, eco2, mode) values (?, ?, ?, ?, ?)", (now, aqi, tvoc, eco2, mode))
    con.commit()
    con.close()


###########################################################

sensor = PiicoDev_ENS160()

while True:
    aqi = sensor.aqi.value
    tvoc = sensor.tvoc
    eco2 = sensor.eco2.value

    insert_sampling(aqi, tvoc, eco2, sensor.operation)

    print('   Date: ' + str(time.time()))
    print('    AQI: ' + str(sensor.aqi.value) + ' [' + str(sensor.aqi.rating) +']')
    print('   TVOC: ' + str(sensor.tvoc) + ' ppb')
    print('   eCO2: ' + str(sensor.eco2.value) + ' ppm [' + str(sensor.eco2.rating) +']')
    print(' Status: ' + sensor.operation)
    print('     Db: Saved')
    print('--------------------------------')
    sys.stdout.flush() # avoid output buffering on stdout
    time.sleep(60)
