import time
from datetime import datetime
import sqlite3
from PiicoDev_ENS160 import PiicoDev_ENS160 # import the device driver
from pathlib import Path
import sys
import signal

def log(message):
    print(f"{str(datetime.fromtimestamp(time.time()))} {message}")

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

class Sample_ENS160():
    """
    operation can be : 'operating ok', 'warm-up', 'initial start-up', 'no valid output', 'fake operating ok', 'turned off'
    """

    def __init__(self) -> None:
        self.operation = 'turned off'

        self.sensor = PiicoDev_ENS160()
        pass

    def sample(self):

        self.valid_data = False
        self.aqi_value = self.sensor.aqi.value
        self.aqi_rating = self.sensor.aqi.rating
        self.tvoc = self.sensor.tvoc
        self.eco2_value = self.sensor.eco2.value
        self.eco2_rating = self.sensor.eco2.rating
        self.operation = self.sensor.operation

        if(self.operation != 'operating ok'):
            return False
        
        if(self.aqi_value == 0 and self.tvoc and self.eco2_value == 0):
            self.operation = 'false positive'
            return False
        
        if(self.operation == 'operating ok'):
            self.valid_data = True
        
        return True

def main():
    log(f"Started")

    retry_time_for_operation = {
        'operating ok': 20,
        'warm-up': 10, 
        'initial start-up': 30, 
        'no valid output': 10, 
        'fake operating ok': 10,
        'turned off': 10
    }

    valid_sleep_time = 60

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
            count += 1
            if(sreader.operation == 'fake operating ok' and count == 3) :
                log(f"rebooting reader")
                count = 0
                del(sreader)
                sreader = Sample_ENS160()

        sys.stdout.flush() # avoid output buffering on stdout
        time.sleep(retry_time_for_operation[sreader.operation])

if __name__ == '__main__':
    signal.signal(signal.SIGINT, interrupt_handler)

    main()