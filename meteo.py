import time
from datetime import datetime
import sqlite3
from pathlib import Path
import sys
import signal

from Sample_BME680 import Sample_BME680

def log(message):
    """Logs a message with timestamp to standard output and flushes the buffer."""
    print(f"{str(datetime.fromtimestamp(time.time()))} {message}")
    sys.stdout.flush()


def interrupt_handler(signum, frame):
    """Gracefully exits the program upon receiving a signal."""
    log(f"Closing for signal {signum} ({signal.Signals(signum).name}).")
    sys.exit(0)

def insert_sampling(metric, value):
    """Inserts a sensor reading into the SQLite database.

    Args:
        metric (str): The name of the sensor metric (temperature, gas, etc.).
        value (float): The measured value for the specified metric.

    Raises:
        ValueError: If the provided metric is not valid.
    """

    VALID_METRICS = ['temperature', 'gas', 'relative_humidity', 'pressure', 'altitude']

    try:
        value = float(value)  # Convert value to float for database storage
    except ValueError:
        raise ValueError(f"'{value}' is not a valid numerical value.")

    metric = str(metric).lower()  # Ensure case-insensitive metric handling
    if metric not in VALID_METRICS:
        raise ValueError(f"'{metric}' is not a valid metric ({', '.join(VALID_METRICS)})")

    con = sqlite3.connect((Path(__file__).resolve().parent / "air.db"))
    cur = con.cursor()

    # Create table only if it doesn't exist yet (idempotent table creation)
    cur.execute("CREATE TABLE IF NOT EXISTS meteo_samples (date INT, metric TEXT, value REAL)")  # Use REAL for decimal values

    now = int(time.time())
    cur.execute("INSERT INTO meteo_samples (date, metric, value) VALUES (?, ?, ?)", (now, metric, value))
    con.commit()
    con.close()


###########################################################

def main():
    
    SAMPLE_FREQUENCY_IN_SECONDS = 1 * 60
    
    """The main function that runs the sensor data collection and logging."""
    log(f"Started")

    sreader = Sample_BME680()
    while True:
        try:
            sample = sreader.sample()

            insert_sampling('temperature', sreader.temperature)
            log(f"Temperature: %0.1f C" % sreader.temperature)

            insert_sampling('gas', sreader.gas)
            log(f"Gas: %d ohm" % sreader.gas)

            insert_sampling('relative_humidity', sreader.relative_humidity)
            log(f"Humidity: %0.1f %%" % sreader.relative_humidity)

            insert_sampling('pressure', sreader.pressure)
            log(f"Pressure: %0.3f hPa" % sreader.pressure)

            insert_sampling('altitude', sreader.altitude)
            log(f"Altitude: %0.2f meters" % sreader.altitude)

            log(f"AQI: %0.2f" % sreader.aqi)

        except Exception as e:
            log(f"Error during sampling: {e}")

        time.sleep(SAMPLE_FREQUENCY_IN_SECONDS)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, interrupt_handler)
    main()