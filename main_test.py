# -*- coding: utf-8 -*-
#  Test.py
#  Luca Knapp

#Eigene Imports

import pasco2
import funktion_db
import hc05lib

#Fremde Imports

import board
import time
from adafruit_bme280 import basic as adafruit_bme280
from smbus2 import SMBus
import pathlib
import json
import os

#FLASK Imports

from flask import Flask, request, redirect, url_for
import threading

##########################################################

app = Flask(__name__)

@app.route("/btn1")
def btn1():
    print("Button 1 gedrückt")
    return redirect("http://raspberrypi.local/Monitoring_V2.html")

@app.route("/btn2")
def btn2():
    print("Button 2 gedrückt")
    return redirect("http://raspberrypi.local/Monitoring_V2.html")

@app.route("/sendtext", methods=["POST"])
def sendtext():
    msg = request.form.get("msg", "")
    print("Empfangen:", msg)
    if msg.startswith("E1"):
        parts = msg.split()
        if(parts[1].isdigit()):
            hc05lib.send_to_device(HC05S[0], parts[1])
            print(f"Gesendet an Einheit 1: {parts[1]}")
    elif msg.startswith("E2"):
        parts = msg.split()
        if(parts[1].isdigit()):
            hc05lib.send_to_device(HC05S[1], parts[1])
            print(f"Gesendet an Einheit 2: {parts[1]}")
    return redirect("http://raspberrypi.local/Monitoring_V2.html")

def start_flask():
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)

#Flask-Server im Hintergrund starten
threading.Thread(target=start_flask, daemon=True).start()

##########################################################

# ------------------------------
# BT-Setup
# ------------------------------

HC05S = [
    "98:D3:C1:FE:93:89",  # HC-05 Einheit 1
    "98:D3:11:FD:6B:9F",  # HC-05 Einheit 2
    #"98:D3:51:FE:B4:D0", # HC-05 Test HC05
]


hc05lib.start_all(HC05S)
time.sleep(2)

device_data = [[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0]]

btstring = ["unit=", "btdata=", "speed=", "cycle=", "period=", "temp_out=", "humi_out=", "temp_in=", "humi_in="]

cmd_write = ["day_name", "month", "day", "time", "year", "ctl"]

fan_percent = 0

# ------------------------------
# Sensor-Setup
# ------------------------------

TMP = pathlib.Path("/var/www/html/latest.json.tmp")
OUT = pathlib.Path("/var/www/html/latest.json")

bus = SMBus(1)
i2c = board.I2C()                                   # für adafruit_bme280
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)   # bme280 initialisierung
bme280.sea_level_pressure = 1013.25                  # Sealevel

delay = 0
delay_time_send = 0

addr_pasco2 = 0x28         # i2c adresse co2 sensor
measure_sec = 10            # Messwerte in Sek. (muss >5 sein)
datasafedelay = 0

pasco2.co2_prodID(addr_pasco2)               # Prod ID anzeigen
pasco2.co2_init(addr_pasco2, measure_sec)    # Initialisierung / Messintervall
pasco2.co2_startmode(addr_pasco2)            # Continuous Mode aktivieren

time.sleep(10)                      # warten, bis erster Messwert fertig ist

def write_json(d):
    TMP.write_text(json.dumps(d, ensure_ascii=False))
    os.replace(TMP, OUT)
    
# ------------------------------
# Hauptschleife
# ------------------------------
try:
    while True:
        
        device_data = hc05lib.readdata(HC05S, btstring, device_data)
        # Kurzer Schlaf, damit die CPU nicht rotiert
        time.sleep(0.1)

        uhrzeit = time.ctime(time.time())
        jetzt = time.time()

        if jetzt >= delay:                  # nur alle measure_sec messen
            delay = jetzt + measure_sec

            try:
                co2 = pasco2.co2_read(addr_pasco2)
            except OSError as e:
                co2 = 0
                print("Fehler beim CO2-Sensor:", e)

            temp = bme280.temperature
            humi = bme280.relative_humidity
            pressure = bme280.pressure
            altitude = bme280.altitude

            print(uhrzeit)
            print(f"CO2: {co2:.2f} ppm")
            print(f"Temperature: {temp:.1f} C")
            print(f"Humidity:    {humi:.1f} %")
            print(f"Pressure:    {pressure:.1f} hPa")
            print(f"Altitude:    {altitude:.2f} m\n")
            
            for i in range(2):
                print(f"Einheit:        {device_data[i][0]}")
                print(f"Temp innen:     {device_data[i][7]} C")
                print(f"Humidity innen: {device_data[i][8]} %")
                print(f"Taussen:        {device_data[i][5]} C")
                print(f"Humidity aussen:{device_data[i][6]} %")
                print(f"Drehzahl:       {device_data[i][2]} U/min")
                print(f"Periode:        {device_data[i][4]}\n")

            data = {"ts": uhrzeit, "co2": co2, "t": temp, "h": humi, "p": pressure,
                    "device1": device_data[0][0], "tempinnen1": device_data[0][5], "huminnen1": device_data[0][6], "tempaussen1": device_data[0][7], "humaussen1": device_data[0][8], "drehzahl1": device_data[0][2], "periode1": device_data[0][4],
                    "device2": device_data[1][0], "tempinnen2": device_data[1][5], "huminnen2": device_data[1][6], "tempaussen2": device_data[1][7], "humaussen2": device_data[1][8], "drehzahl2": device_data[1][2], "periode2": device_data[1][4],
                    }
                    
            write_json(data)  # für Website
            
            datasafedelay = datasafedelay + 1 
            if datasafedelay >= 90: # alle 15 Minuten speichern 
                funktion_db.databasesafe("raspi", uhrzeit, round(co2, 2), round(temp, 2), round(humi, 2), round(pressure, 2), 0, 0, 0, 0)
                for idx, row in enumerate(device_data): # schaut ob Daten vorhanden sind
                    if row and all(row[i] not in (None, "", 0) for i in (0, 6, 7, 8)):
                        funktion_db.databasesafe(   f"ardu{row[0]}", uhrzeit, 0, 0, 0, 0, row[7], row[8], row[5], row[6]
                        )
                datasafedelay = 0    
            #Speichern in der DB (Tabelle je Monat)

            for p in range(len(HC05S)):
                if co2 == 0:
                    # Sensorfehler ? Fallback
                    fan_percent = 50
                    hc05lib.send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")
                    mode = "FALLBACK"

                elif co2 < 700:
                    fan_percent = 25
                    hc05lib.send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")
                    mode = "IDLE"

                elif 700 <= co2 < 1200:
                    # Lüfterleistung steigt linear zwischen 20?80 %
                    fan_percent = 25 + (co2 - 700) * (60 / 500)
                    hc05lib.send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")
                    mode = "NORMAL"

                elif co2 >= 1200:
                    fan_percent = 90   # Vollgas
                    hc05lib.send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")
                    mode = "BOOST"
                    
                    # Feuchte-Override
                if humi > 60:
                    fan_percent = max(fan_percent, 60)
                    hc05lib.send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")
                    mode = "HUMIDITY"

        if jetzt >= delay_time_send: #Tag=Mon, Monat=Jan, Tag=01, Zeit=12:00:00, Jahr=2025 an die Einheiten gesendet
            parts = uhrzeit.split()
            for p in range(len(HC05S)):
                for i in range(len(parts)):
                    hc05lib.send_to_device(HC05S[p], f"{cmd_write[i]}={parts[i]}")
                    time.sleep(0.1)
                    #print(f"Gesendet an Einheit {p+1}: {cmd_write[i]}={parts[i]}")
            print(f"Zeit-Sync gesendet: {uhrzeit}\n")
            delay_time_send = jetzt +  3600  # alle 60 Minuten
        

except KeyboardInterrupt:
    print("Beende auf Wunsch (Ctrl+C)...")

finally:
    try:
        bus.close()
        hc05lib.stop_all()
    except Exception:
        pass
    print("Alles gestoppt.")
