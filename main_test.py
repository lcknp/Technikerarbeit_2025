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

# Anzahl der Datenpunkte pro Gerät (z. B. Sensorwerte)
data_points = 9

# device_data automatisch generieren
device_data = [[0] * data_points for _ in HC05S]

hc05lib.start_all(HC05S)
time.sleep(5) #Warte bis HC05 bereit ist

# Variablen für BT-Daten

cmd_read = ["unit=", "btdata=", "speed=", "cycle=", "period=", "temp_out=", "humi_out=", "temp_in=", "humi_in="]

cmd_write = ["day_name", "month", "day", "time", "year", "ctl", "delay", "rasp_read"]

fan_percent = 0

# ------------------------------
# Sensor-Setup
# ------------------------------

TMP = pathlib.Path("/var/www/html/latest.json.tmp")
OUT = pathlib.Path("/var/www/html/latest.json")

bus = SMBus(1)
i2c = board.I2C()                                   # für adafruit_bme280
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)   # bme280 initialisierung
bme280.sea_level_pressure = 1000                  # Sealevel

delay = 0
delay_time_send = 0
datasafedelay = 0

co2 = pasco2.pasco2init()

def write_json(d):
    TMP.write_text(json.dumps(d, ensure_ascii=False))
    os.replace(TMP, OUT)
    
# ------------------------------
# Hauptschleife
# ------------------------------
try:
    while True:

        uhrzeit = time.ctime(time.time())
        jetzt = time.time()

        co2 = pasco2.read_co2()

        try:
            temp = bme280.temperature
            humi = bme280.humidity
            pressure = bme280.pressure
            altitude = bme280.altitude
        except OSError: # I2C Fehler
            print("BME280 Fehler")
            None

        if jetzt >= delay:      
            delay = jetzt + 1   # + x Sekunden

            jetzt = time.localtime()

            wochentag = jetzt.tm_wday  # Montag = 0, Sonntag = 6
            stunde = jetzt.tm_hour     # 0 bis 23

            if wochentag < 5:  # Montag bis Freitag
                if 6 <= stunde < 18:
                    hc05lib.writedata(HC05S, cmd_write, co2)  #Lüfterstufe an alle Geräte senden
                elif 4 <= stunde < 6:
                    hc05lib.writedata(HC05S, cmd_write, co2)  #Lüfterstufe an alle Geräte senden
                else:
                    hc05lib.write_off(HC05S, cmd_write)
            else:
                hc05lib.write_off(HC05S, cmd_write)

            print(uhrzeit)
            print(f"CO2: {co2:.2f} ppm")
            print(f"Temperature: {temp:.1f} C")
            print(f"Humidity:    {humi:.1f} %")
            print(f"Pressure:    {pressure:.1f} hPa")
            print(f"Altitude:    {altitude:.2f} m\n")
            
            for i in range(len(HC05S)):
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
            if datasafedelay >= 1: # alle Sekunde
                funktion_db.databasesafe("raspi", uhrzeit, round(co2, 2), round(temp, 2), round(humi, 2), round(pressure, 2), 0, 0, 0, 0)
                for idx, row in enumerate(device_data): # schaut ob Daten vorhanden sind
                    if row and all(row[i] not in (None, "", 0) for i in (0, 4, 6, 7, 8)):
                        funktion_db.databasesafe(   f"ardu{row[0]}", uhrzeit, 0, 0, 0, row[4], row[7], row[8], row[5], row[6]
                        )
                datasafedelay = 0    
            #Speichern in der DB (Tabelle je Monat)

            hc05lib.send_to_device(HC05S[0], f"{cmd_write[7]}=")
            hc05lib.send_to_device(HC05S[1], f"{cmd_write[7]}=")

        # BT-Daten von den Einheiten lesen

        device_data = hc05lib.readdata(HC05S, cmd_read, cmd_write, device_data)

        # Zeit-Sync an die Einheiten senden

        hc05lib.time_sync(HC05S, cmd_write)
        

except KeyboardInterrupt:
    print("Beende auf Wunsch (Ctrl+C)...")

finally:
    try:
        hc05lib.stop_all()
        pasco2.write_value(pasco2.REG_MEAS_CFG, pasco2.read_value(pasco2.REG_MEAS_CFG) & 0b11111100) # set mode to idle
        pasco2.bus.close()
        bus.close()
    except Exception:
        pass
    print("Alles gestoppt.")