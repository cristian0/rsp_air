import time
from datetime import datetime
import sqlite3
from pathlib import Path
import sys
import signal

from Sample_ENS160 import Sample_ENS160


def log(message):
    print(f"{str(datetime.fromtimestamp(time.time()))} {message}")
    sys.stdout.flush()

def interrupt_handler(signum, frame):
    log(f"Closing for signal {signum} ({signal.Signals(signum).name}).")
    sys.exit(0)

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

def main():
    log(f"Started")

    retry_time_for_operation = {
        'operating ok': 60,
        'warm-up': 10,
        'initial start-up': 60, 
        'no valid output': 10, 
        'fake operating ok': 10,
        'turned off': 10
    }

    sreader = Sample_ENS160()

    count = 0
    while True:
        sample = sreader.sample()
        print((sample, sreader.aqi_value, sreader.tvoc, sreader.eco2_value, sreader.operation))
        if(sample != False):
            insert_sampling(sreader.aqi_value, sreader.tvoc, sreader.eco2_value, sreader.operation)
            log(f"Sampled AQI:{str(sreader.aqi_value)} TVOC:{str(sreader.tvoc)}ppb eCO2:{str(sreader.eco2_value)}ppm")
        else:
            log(f"Mode: '{sreader.operation}', not sampling")
            # count += 1
            # if(sreader.operation == 'no valid output' and count == 3) :
            #     log(f"rebooting reader")
            #     count = 0
                # del(sreader)
                # sreader = Sample_ENS160()

        time.sleep(retry_time_for_operation[sreader.operation])

if __name__ == '__main__':
    signal.signal(signal.SIGINT, interrupt_handler)

    main()