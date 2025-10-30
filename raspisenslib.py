#
#

from smbus2 import SMBus
from adafruit_bme280 import basic as adafruit_bme280
import pasco2

old_raspi_data = [0, 0, 0, 0, 0]
def raspi_readdata(bme280):
    global old_raspi_data

    # Starte mit den alten Werten
    raspi_data = old_raspi_data.copy()

    raspi_data[0] = pasco2.read_co2()
    
    try:
        raspi_data[1] = bme280.temperature
        raspi_data[2] = bme280.humidity
        raspi_data[3] = bme280.pressure
        raspi_data[4] = bme280.altitude
    except OSError:
        print("BME280 Fehler")

    old_raspi_data = raspi_data.copy()
    return raspi_data
