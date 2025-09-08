# pasco2.py

from smbus2 import SMBus

bus = SMBus(1)

def co2_prodID(i2c_adresse):
    #Produkt ID vom Co2 sensor 0x10
    PROD_ID = 0x00
    
    prod = bus.read_i2c_block_data(i2c_adresse, PROD_ID, 1)[0]
    PROD_ID = prod
    print(f"Prod_ID:{hex(PROD_ID)}")


def co2_init(i2c_adresse, sec):
    # Funktion Messrate auf setzen (>5 sec Funkioniert am besten)
    REG_RATE_H, REG_RATE_L = 0x02, 0x03
    
    bus.write_byte_data(i2c_adresse, REG_RATE_H, (sec >> 8) & 0xFF)
    bus.write_byte_data(i2c_adresse, REG_RATE_L, sec & 0xFF)

def co2_startmode(i2c_adresse):
    REG_CFG = 0x04
    
    bus.write_byte_data(i2c_adresse, REG_CFG, 0x02) # Continuous Mode starten


def co2_read(i2c_adresse):
    REG_CO2_H = 0x05 #Register Daten PASCO2
    
    msb, lsb = bus.read_i2c_block_data(i2c_adresse, REG_CO2_H, 2)
    value = (msb << 8) | lsb
    if value & 0x8000:  # signed 16-bit
        value -= 65536
    
    return value
