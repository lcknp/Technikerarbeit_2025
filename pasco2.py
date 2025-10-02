# pasco2.py
# Luca Knapp
# Bibliothek für den CO2-Sensor PASCO2
# Source code GitHub: https://github.com/domenk/pasco2

import time
import smbus

SENSOR_I2C_ADDR = 0x28

# Register-Adressen

REG_PROD_ID     = 0x00 # Product and revision ID
REG_SENS_STS    = 0x01 # Sensor status
REG_MEAS_RATE_H = 0x02 # Measurement rate, high byte
REG_MEAS_RATE_L = 0x03 # Measurement rate, low byte
REG_MEAS_CFG    = 0x04 # Measurement configuration
REG_CO2PPM_H    = 0x05 # CO2 concentration, high byte
REG_CO2PPM_L    = 0x06 # CO2 concentration, low byte
REG_MEAS_STS    = 0x07 # Measurement status
REG_INT_CFG     = 0x08 # Interrupt configuration
REG_ALARM_TH_H  = 0x09 # Alarm threshold, high byte
REG_ALARM_TH_L  = 0x0A # Alarm threshold, low byte
REG_PRESS_REF_H = 0x0B # Pressure reference, high byte
REG_PRESS_REF_L = 0x0C # Pressure reference, low byte
REG_CALIB_REF_H = 0x0D # Calibration reference, high byte
REG_CALIB_REF_L = 0x0E # Calibration reference, low byte
REG_SCRATCH_PAD = 0x0F # Scratch pad
REG_SENS_RST    = 0x10 # Sensor reset

REG_MEAS_CFG_OP_MODE = {0b00: "idle", 0b01: "single-shot", 0b10: "continuous", 0b11: "reserved"}

concentration_waiting = False
co2 = 0

def read_value(register):
	value = bus.read_i2c_block_data(SENSOR_I2C_ADDR, register, 1)
	return value[0]

def read_value_double(register):
	value = bus.read_i2c_block_data(SENSOR_I2C_ADDR, register, 2)
	return (value[0] << 8) | value[1]

def write_value(register, value):
	bus.write_i2c_block_data(SENSOR_I2C_ADDR, register, [value])
	time.sleep(0.1)

def write_value_double(register, value):
	bus.write_i2c_block_data(SENSOR_I2C_ADDR, register, [value >> 8, value & 0b11111111])
	time.sleep(0.1)

def sensor_set_measurement_rate(rate): # rate = seconds
	write_value(REG_MEAS_CFG, read_value(REG_MEAS_CFG) & 0b11111100) # set mode to idle
	time.sleep(1)

	write_value_double(REG_MEAS_RATE_H, rate)

	write_value(REG_MEAS_CFG, (read_value(REG_MEAS_CFG) & 0b11111100) | 0b10) # set mode to continuous
	time.sleep(1)

bus = smbus.SMBus(1)

def pasco2init():
	
    write_value_double(REG_MEAS_RATE_H, 10) # Messrate 10 Sekunden
    write_value(REG_MEAS_CFG, 0b10) # set mode to continuous
    
    sensor_prod_id = read_value(REG_PROD_ID)
    print("--- Product and revision ID ---")
    print("Product ID: {}".format((sensor_prod_id >> 5) & 0b111))
    print("Revision ID: {}".format(sensor_prod_id & 0b11111))
    print("")

    sensor_meas_rate = read_value_double(REG_MEAS_RATE_H)
    sensor_meas_sts = read_value(REG_MEAS_STS) # reading MEAS_CFG resets DRDY in MEAS_STS, so we read MEAS_STS first
    sensor_meas_cfg = read_value(REG_MEAS_CFG)
    print("--- Measurement ---")
    print("Measurement period: {} s".format(sensor_meas_rate))
    print("Operating mode: {}".format(REG_MEAS_CFG_OP_MODE[sensor_meas_cfg & 0b11]))
    print("")

    write_value_double(REG_PRESS_REF_H, 950) # Pressure compensation
    print("--- Pressure compensation ---")
    print("Pressure: {} hPa".format(read_value_double(REG_PRESS_REF_H)))
    print("")

    print("--- Automatic baseline offset compensation ---")
    print("ABOC: {} ppm".format(read_value_double(REG_CALIB_REF_H)))
    print("")

    print("--- CO2 concentration ---")
    print("{} ppm".format(read_value_double(REG_CO2PPM_H)))
    co2 = read_value_double(REG_CO2PPM_H)

    return co2

def read_co2():
        global concentration_waiting
        global co2
        
        try:
            if ((read_value(REG_MEAS_STS) >> 4) & 0b1) == 1:
                if concentration_waiting:
                    concentration_waiting = False
                co2 = read_value_double(REG_CO2PPM_H)
            if not concentration_waiting:
                print("Warte auf CO2 Werte")
                concentration_waiting = True
        except OSError: # I2C Fehler
                None

        return co2

# soft reset

def sensor_soft_reset():
    write_value(REG_SENS_RST, 0xA3) # soft reset
    write_value(REG_SENS_RST, 0xBC) # reset ABOC context
    write_value(REG_SENS_RST, 0xCF) # force-save calibration offset to non-volatile memory
    write_value(REG_SENS_RST, 0xDF) # disable Stepwise Reactive IIR Filter
    write_value(REG_SENS_RST, 0xFE) # enable Stepwise Reactive IIR Filter
    write_value(REG_SENS_RST, 0xFC) # reset forced calibration correction factor
    time.sleep(1)

