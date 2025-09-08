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

#Fremde Imports

import pathlib
import json
import os

#FLASK Imports

from flask import Flask, request
import threading

##########################################################

app = Flask(__name__)

@app.after_request
def add_cors_headers(resp):
    # Für den Start offen lassen; später spezifische Origin setzen:
    # resp.headers["Access-Control-Allow-Origin"] = "http://192.168.2.136"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

@app.route("/btn1")
def btn1():
    print("Button 1 gedrückt")
    return "Button 1 OK"

@app.route("/btn2")
def btn2():
    print("Button 2 gedrückt")
    return "Button 2 OK"

# Text vom Client entgegennehmen (POST oder GET)
@app.route("/sendtext", methods=["GET", "POST", "OPTIONS"])
def sendtext():
    if request.method == "OPTIONS":
        return ("", 204)  # CORS Preflight

    # akzeptiere form-POST, JSON-POST und GET-Query
    msg = (
        request.form.get("msg") or
        (request.get_json(silent=True) or {}).get("msg") or
        request.args.get("msg", "")
    )

    print("Text empfangen:", msg)   # <-- hier in deine Unterfunktion weitergeben
    # my_sub_function(msg)

    return f"Empfangen: {msg}"

def start_flask():
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)

# Flask-Server im Hintergrund starten
threading.Thread(target=start_flask, daemon=True).start()

##########################################################

# ------------------------------
# BT-Setup
# ------------------------------

HC05S = [
    "98:D3:C1:FE:93:89",  # HC-05 Einheit 1
    #"98:D3:11:FD:6B:9F",  # HC-05 Einheit 2
    "98:D3:51:FE:B4:D0", # HC-05 Test HC05
]


hc05lib.start_all(HC05S)
time.sleep(2)

device_data = [[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0]]

btstring = ["Einheit", "BTData", "Drehzahl", "Cycle", "Periode", "Temp_Innen", "Humi_Innen", "Temp_Aussen", "Humi_Aussen"]


# ------------------------------
# Sensor-Setup
# ------------------------------

TMP = pathlib.Path("/var/www/html/latest.json.tmp")
OUT = pathlib.Path("/var/www/html/latest.json")

bus = SMBus(1)
i2c = board.I2C()                                   # für adafruit_bme280
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)   # bme280 initialisierung
bme280.sea_level_pressure = 1013.25                  # Sealevel

delay = 0  # start delay

addr_pasco2 = 0x28         # i2c adresse co2 sensor
measure_sec = 6            # Messwerte in Sek. (muss >5 sein)

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
        
        jetzt = time.time()
        if jetzt >= delay:                  # nur alle measure_sec messen
            delay = jetzt + measure_sec

            uhrzeit = time.ctime(time.time())

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
                print(f"Temp innen:     {device_data[i][5]} C")
                print(f"Humidity innen: {device_data[i][6]} %")
                print(f"Taussen:        {device_data[i][7]} C")
                print(f"Humidity innen: {device_data[i][8]} %")
                print(f"Drehzahl:       {device_data[i][2]} U/min")
                print(f"Periode:        {device_data[i][4]}\n")

            data = {"ts": uhrzeit, "co2": co2, "t": temp, "h": humi, "p": pressure,
                    "device1": device_data[0][0], "tempinnen1": device_data[0][5], "huminnen1": device_data[0][6], "tempaussen1": device_data[0][7], "humaussen1": device_data[0][8], "drehzahl1": device_data[0][2], "periode1": device_data[0][4],
                    "device2": device_data[1][0], "tempinnen2": device_data[1][5], "huminnen2": device_data[1][6], "tempaussen2": device_data[1][7], "humaussen2": device_data[1][8], "drehzahl2": device_data[1][2], "periode2": device_data[1][4],
                    }
                    
            write_json(data)  # für Website

            funktion_db.databasesafe("raspi", uhrzeit, co2, temp, humi, pressure)
            funktion_db.databasesafe("ardu1", uhrzeit, 0, device_data[0][5], device_data[0][6], 0)
            funktion_db.databasesafe("ardu2", uhrzeit, 0, device_data[1][5], device_data[1][6], 0)
            
            # Speichern in der DB (Tabelle je Monat)
        
        # Kurzer Schlaf, damit die CPU nicht rotiert
        time.sleep(0.05)

except KeyboardInterrupt:
    print("Beende auf Wunsch (Ctrl+C)...")

finally:
    try:
        bus.close()
        hc05lib.stop_all()
    except Exception:
        pass
    print("Alles gestoppt.")
