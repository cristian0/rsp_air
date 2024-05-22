
from PiicoDev_ENS160 import PiicoDev_ENS160 # import the device driver

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
        
        if(self.aqi_value == 0):
            self.operation = 'no valid output'
            return False
        
        if(self.operation == 'operating ok'):
            self.valid_data = True
        
        return True
