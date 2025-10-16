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

raspi_data = [0,0,0,0,0]

# Variablen für BT-Daten

cmd_read = ["unit=", "btdata=", "speed=", "cycle=", "period=", "temp_out=", "humi_out=", "temp_in=", "humi_in="]

cmd_write = ["day_name", "month", "day", "time", "year", "ctl", "toggle", "rasp_read"]

hc05lib.start_all(HC05S)
time.sleep(5) #Warte bis HC05 bereit ist

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
    
old_raspi_data = [0, 0, 0, 0, 0]
def raspi_readdata():
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

def build_web_payload(uhrzeit, raspi_data, device_data):
    payload = {
        "ts": uhrzeit,
        "co2": raspi_data[0],
        "t": raspi_data[1],
        "h": raspi_data[2],
        "p": raspi_data[3],
    }

    # Für jedes Gerät in der Liste device_data hinzufügen
    for i, dev in enumerate(device_data, start=1):
        payload.update({
            f"device{i}": dev[0],
            f"tempinnen{i}": dev[5],
            f"huminnen{i}": dev[6],
            f"tempaussen{i}": dev[7],
            f"humaussen{i}": dev[8],
            f"drehzahl{i}": dev[2],
            f"periode{i}": dev[4],
        })

    return payload


# ------------------------------
# Hauptschleife
# ------------------------------
try:
    while True:

        uhrzeit = time.ctime(time.time())
        jetzt = time.time()

        raspi_data = raspi_readdata()

        if jetzt >= delay:      
            delay = jetzt + 1   # + x Sekunden

            uhrzeit_prüf = time.localtime()

            wochentag = uhrzeit_prüf.tm_wday  # Montag = 0, Sonntag = 6
            stunde = uhrzeit_prüf.tm_hour     # 0 bis 23

            # Sendet Laufrichtung an die Einheiten
            # Lüfterstufe an alle Geräte senden
            # 1 = Montag bis 5 = Freitag
            if wochentag < 6:  
                if 6 <= stunde < 18:
                    hc05lib.writedata(HC05S, cmd_write, raspi_data, device_data)  
                elif 4 <= stunde < 6:
                    hc05lib.writedata(HC05S, cmd_write, raspi_data, device_data)  
                else:
                    hc05lib.write_off(HC05S, cmd_write)
            else:
                hc05lib.write_off(HC05S, cmd_write)

            print(uhrzeit)
            print(f"CO2: {raspi_data[0]:.2f} ppm")
            print(f"Temperature: {raspi_data[1]:.1f} C")
            print(f"Humidity:    {raspi_data[2]:.1f} %")
            print(f"Pressure:    {raspi_data[3]:.1f} hPa")
            print(f"Altitude:    {raspi_data[4]:.2f} m\n")
            
            for i in range(len(HC05S)):
                print(f"Einheit:        {device_data[i][0]}")
                print(f"Temp innen:     {device_data[i][7]} C")
                print(f"Humidity innen: {device_data[i][8]} %")
                print(f"Taussen:        {device_data[i][5]} C")
                print(f"Humidity aussen:{device_data[i][6]} %")
                print(f"Drehzahl:       {device_data[i][2]} U/min")
                print(f"Periode:        {device_data[i][4]}\n")

            # Erstellt ein Dict und schreibt es in eine JSON Datei
            data = build_web_payload(uhrzeit, raspi_data, device_data)
            write_json(data)
            
            # Speichern in der DB
            datasafedelay = datasafedelay + 1 
            if datasafedelay >= 1: # alle Sekunde
                funktion_db.save_to_db(uhrzeit, raspi_data, device_data)
                datasafedelay = 0    
            
            # Schreibt je nach Intervall die Einheiten an um Daten zu lesesn
            for i in range(len(HC05S)):
                hc05lib.send_to_device(HC05S[i], f"{cmd_write[7]}=")

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