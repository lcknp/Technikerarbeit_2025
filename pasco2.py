# =============================================================================
#  Projekt:      EBM-Papst Lüftungssteuerung – Technikerarbeit 2025/26
#  Datei:        pasco2.py
#  Autor:        Luca Knapp
#  Version:      1.0
#  Datum:        2025
#
#  Beschreibung:
#  ---------------------------------------------------------------------------
#  Bibliothek zur Ansteuerung des PASCO2 CO₂-Sensors über I2C.
#  Grundlage: https://github.com/domenk/pasco2
#
#  Lizenz:
#   Dieses Projekt wurde im Rahmen der Technikerarbeit 2025/26 erstellt.
#   Nutzung und Weitergabe nur mit Erlaubnis des Autors.
#
# =============================================================================

import time

import smbus

SENSOR_I2C_ADDR = 0x28

# Register-Adressen

REG_PROD_ID = 0x00  # Product and revision ID
REG_SENS_STS = 0x01  # Sensor status
REG_MEAS_RATE_H = 0x02  # Measurement rate, high byte
REG_MEAS_RATE_L = 0x03  # Measurement rate, low byte
REG_MEAS_CFG = 0x04  # Measurement configuration
REG_CO2PPM_H = 0x05  # CO2 concentration, high byte
REG_CO2PPM_L = 0x06  # CO2 concentration, low byte
REG_MEAS_STS = 0x07  # Measurement status
REG_INT_CFG = 0x08  # Interrupt configuration
REG_ALARM_TH_H = 0x09  # Alarm threshold, high byte
REG_ALARM_TH_L = 0x0A  # Alarm threshold, low byte
REG_PRESS_REF_H = 0x0B  # Pressure reference, high byte
REG_PRESS_REF_L = 0x0C  # Pressure reference, low byte
REG_CALIB_REF_H = 0x0D  # Calibration reference, high byte
REG_CALIB_REF_L = 0x0E  # Calibration reference, low byte
REG_SCRATCH_PAD = 0x0F  # Scratch pad
REG_SENS_RST = 0x10  # Sensor reset

# Messmodus-Register
REG_MEAS_CFG_OP_MODE = {
    0b00: "idle",
    0b01: "single-shot",
    0b10: "continuous",
    0b11: "reserved",
}

# Interne Statusvariablen
concentration_waiting = False
co2 = 0

# I2C-Bus initialisieren
bus = smbus.SMBus(1)


# Hilfsfunktionen zum Lesen und Schreiben von Registerwerten
def read_value(register):
    value = bus.read_i2c_block_data(SENSOR_I2C_ADDR, register, 1)
    return value[0]


# Hilfsfunktionen zum Lesen und Schreiben von Registerwerten 16-Bit-Werts
def read_value_double(register):
    value = bus.read_i2c_block_data(SENSOR_I2C_ADDR, register, 2)
    return (value[0] << 8) | value[1]


# Hilfsfunktionen zum Lesen und Schreiben von Registerwerten
def write_value(register, value):
    bus.write_i2c_block_data(SENSOR_I2C_ADDR, register, [value])
    time.sleep(0.1)


# Hilfsfunktionen zum Lesen und Schreiben von Registerwerten 16-Bit-Werts
def write_value_double(register, value):
    bus.write_i2c_block_data(
        SENSOR_I2C_ADDR,
        register,
        [value >> 8, value & 0b11111111],
    )
    time.sleep(0.1)


# Setzt die Messrate in Sekunden
def sensor_set_measurement_rate(rate):
    write_value(REG_MEAS_CFG, read_value(REG_MEAS_CFG) & 0b11111100)
    time.sleep(1)

    write_value_double(REG_MEAS_RATE_H, rate)

    write_value(
        REG_MEAS_CFG,
        (read_value(REG_MEAS_CFG) & 0b11111100) | 0b10,
    )
    time.sleep(1)


# Initialisiert den Sensor
def pasco2init():
    write_value_double(REG_MEAS_RATE_H, 10)
    write_value(REG_MEAS_CFG, 0b10)

    sensor_prod_id = read_value(REG_PROD_ID)
    print("--- Product and revision ID ---")
    print(f"Product ID: {(sensor_prod_id >> 5) & 0b111}")
    print(f"Revision ID: {sensor_prod_id & 0b11111}\n")

    sensor_meas_rate = read_value_double(REG_MEAS_RATE_H)
    sensor_meas_sts = read_value(REG_MEAS_STS)
    sensor_meas_cfg = read_value(REG_MEAS_CFG)

    print("--- Measurement ---")
    print(f"Measurement period: {sensor_meas_rate} s")
    print(
        "Operating mode: "
        f"{REG_MEAS_CFG_OP_MODE[sensor_meas_cfg & 0b11]}\n"
    )

    write_value_double(REG_PRESS_REF_H, 950)
    print("--- Pressure compensation ---")
    print(f"Pressure: {read_value_double(REG_PRESS_REF_H)} hPa\n")

    print("--- Automatic baseline offset compensation ---")
    print(f"ABOC: {read_value_double(REG_CALIB_REF_H)} ppm\n")

    print("--- CO2 concentration ---")
    print(f"{read_value_double(REG_CO2PPM_H)} ppm")

    global co2
    co2 = read_value_double(REG_CO2PPM_H)
    return co2


# Liest den CO2-Wert aus dem Sensor
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

    except OSError:
        pass

    return co2


# Führt einen Soft-Reset des Sensors durch
def sensor_soft_reset():
    write_value(REG_SENS_RST, 0xA3)
    write_value(REG_SENS_RST, 0xBC)
    write_value(REG_SENS_RST, 0xCF)
    write_value(REG_SENS_RST, 0xDF)
    write_value(REG_SENS_RST, 0xFE)
    write_value(REG_SENS_RST, 0xFC)
    time.sleep(1)