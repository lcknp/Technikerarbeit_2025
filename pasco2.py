# pasco2.py

from smbus2 import SMBus

_bus = SMBus(1)  # interner Bus (optional)

def co2_prodID(i2c_adresse):
    PROD_ID_REG = 0x00
    val = _bus.read_byte_data(i2c_adresse, PROD_ID_REG)
    print(f"Prod_ID: {hex(val)}")   # Erwartet: 0xf4
    return val

def co2_init(i2c_adresse, sec):
    # Messintervall setzen (Empfehlung: >=5 s)
    REG_RATE_H, REG_RATE_L = 0x02, 0x03
    sec = max(5, int(sec))  # absichern
    _bus.write_byte_data(i2c_adresse, REG_RATE_H, (sec >> 8) & 0xFF)
    _bus.write_byte_data(i2c_adresse, REG_RATE_L, sec & 0xFF)

def co2_startmode(i2c_adresse):
    REG_CFG = 0x04
    _bus.write_byte_data(i2c_adresse, REG_CFG, 0x02)  # Continuous Mode

def co2_read(i2c_adresse):
    REG_CO2_H = 0x05
    msb, lsb = _bus.read_i2c_block_data(i2c_adresse, REG_CO2_H, 2)
    value = (msb << 8) | lsb          # CO2 ist **unsigned**
    return value                       # ppm
