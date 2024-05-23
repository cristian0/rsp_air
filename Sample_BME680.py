import adafruit_bme680
import board
import math

class Sample_BME680():
    """
    A class to interact with the BME680 sensor using the Adafruit BME680 library.
    """

    def __init__(self) -> None:
        i2c = board.I2C()   # uses board.SCL and board.SDA
        self.sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c)
        self.sensor.sea_level_pressure = 1013.25
        pass

    def sample(self):

        self.temperature = self.sensor.temperature
        self.gas = self.sensor.gas
        self.relative_humidity = self.sensor.relative_humidity
        self.pressure = self.sensor.pressure
        self.altitude = self.sensor.altitude
        self.aqi = math.log(self.sensor.gas) + 0.04 * self.sensor.relative_humidity

        return True
