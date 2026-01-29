# =============================================================================
#  Projekt:      EBM-Papst Lüftungssteuerung – Technikerarbeit 2025/26
#  Datei:        main.py
#  Autor:        Luca Knapp
#  Version:      2.5.1
#  Datum:        2025
#
#  Beschreibung:
#  ---------------------------------------------------------------------------
#  Dieses Skript ist die zentrale Steuerungslogik für das gesamte Projekt.
#  Es übernimmt folgende Hauptaufgaben:
#
#   • Bluetooth-Kommunikation mit zwei oder mehreren HC-05 basierten Sensoreinheiten
#   • Einlesen von Temperatur, Luftfeuchte, CO2, Luftdruck (Raspberry + Sensoren)
#   • Automatische Lüftersteuerung basierend auf Zeit, Wochentag und Sensorwerten
#   • Schreiben von Live-Daten in eine JSON-Datei für die Weboberfläche
#   • Speichern der Messwerte in einer SQL-Datenbank
#   • Zeit-Synchronisation mit den Einheiten
#
#  Aufbau:
#   - HC-05 Verbindung wird aufgebaut und verwaltet
#   - BME280 und PASCO2 Sensoren werden initialisiert
#   - Hauptschleife läuft und liest alle x Sekunden die Sensorwerte ein
#   - Daten werden verarbeitet, angezeigt und gespeichert
#
#  Lizenz:
#   Dieses Projekt wurde im Rahmen der Technikerarbeit 2025/26 erstellt.
#   Nutzung und Weitergabe nur mit Erlaubnis des Autors.
#
# =============================================================================

import pathlib
import time

import board
from adafruit_bme280 import basic as adafruit_bme280
from smbus2 import SMBus

import database
import hc05lib
import pasco2
import raspisenslib
import weblib

# ------------------------------
# BT-Setup
# ------------------------------

HC05S = [
    "98:D3:C1:FE:93:89",  # HC-05 Einheit 1
    "98:D3:11:FD:6B:9F",  # HC-05 Einheit 2
    # "98:D3:51:FE:B4:D0", # HC-05 Test HC05
]

# Anzahl der Datenpunkte pro Gerät (z. B. Sensorwerte)
DATA_POINTS = 9

# device_data automatisch generieren
device_data = [[0] * DATA_POINTS for _ in HC05S]

raspi_data = [0, 0, 0, 0, 0]

# Konstanten für BT-Daten
CMD_READ = [
    "unit=",
    "btdata=",
    "speed=",
    "cycle=",
    "period=",
    "temp_out=",
    "humi_out=",
    "temp_in=",
    "humi_in=",
]

CMD_WRITE = [
    "day_name",
    "month",
    "day",
    "time",
    "year",
    "ctl",
    "toggle",
    "rasp_read",
]

hc05lib.start_all(HC05S)
time.sleep(5)  # Warte bis HC05 bereit ist

# ------------------------------
# Sensor-Setup
# ------------------------------

TMP = pathlib.Path("/var/www/html/latest.json.tmp")
OUT = pathlib.Path("/var/www/html/latest.json")

bus = SMBus(1)
i2c = board.I2C()  # für adafruit_bme280
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)  # bme280 initialisierung
bme280.sea_level_pressure = 900  # Sealevel
co2 = pasco2.pasco2init()  # PASCO2 Initialisierung

delay = 0
delay_time_send = 0
datasafedelay = 0

# Initiales Einlesen der Sensorwerte
raspi_data = raspisenslib.raspi_readdata(bme280)

# ------------------------------
# Hauptschleife
# ------------------------------
try:
    while True:
        uhrzeit = time.ctime(time.time())
        jetzt = time.time()

        # Raspi-Sensorwerte einlesen
        raspi_data = raspisenslib.raspi_readdata(bme280)

        # Alle x Sekunden die Steuerung ausführen
        if jetzt >= delay:
            delay = jetzt + 1  # + x Sekunden

            uhrzeit_pruef = time.localtime()

            wochentag = uhrzeit_pruef.tm_wday  # Montag = 0, Sonntag = 6
            stunde = uhrzeit_pruef.tm_hour  # 0 bis 23

            # Sendet Laufrichtung an die Einheiten
            # Lüfterstufe an alle Geräte senden
            # 1 = Montag bis 5 = Freitag
            if wochentag < 7:
                if 6 <= stunde < 20:
                    hc05lib.writedata(
                        HC05S, CMD_WRITE, raspi_data, device_data
                    )
                elif 5 <= stunde < 6:
                    stosslueften = raspi_data.copy()
                    stosslueften[0] = 1000  # CO2 auf 1000 ppm setzen für Stosslüften
                    hc05lib.writedata(
                        HC05S, CMD_WRITE, stosslueften, device_data
                    )
                else:
                    hc05lib.write_off(HC05S, CMD_WRITE)
            else:
                hc05lib.write_off(HC05S, CMD_WRITE)

            # Ausgabe der Raspi-Daten
            print(uhrzeit)
            print(f"CO2: {raspi_data[0]:.2f} ppm")
            print(f"Temperature: {raspi_data[1]:.1f} C")
            print(f"Humidity:    {raspi_data[2]:.1f} %")
            print(f"Pressure:    {raspi_data[3]:.1f} hPa")
            print(f"Altitude:    {raspi_data[4]:.2f} m\n")

            # Ausgabe der Daten der Einheiten
            for i in range(len(HC05S)):
                print(f"Einheit:        {device_data[i][0]}")
                print(f"Temp innen:     {device_data[i][7]} C")
                print(f"Humidity innen: {device_data[i][8]} %")
                print(f"Taussen:        {device_data[i][5]} C")
                print(f"Humidity aussen:{device_data[i][6]} %")
                print(f"Drehzahl:       {device_data[i][2]} U/min")
                print(f"Periode:        {device_data[i][4]}\n")

            # Erstellt ein Dict und schreibt es in eine JSON Datei
            data = weblib.build_web_payload(uhrzeit, raspi_data, device_data)
            weblib.write_json(data, TMP, OUT)

            # Speichern in der DB
            datasafedelay += 1
            if datasafedelay >= 20:  # alle 20 Sekunden speichern
                database.save_to_db(uhrzeit, raspi_data, device_data)
                datasafedelay = 0

            # Schreibt je nach Intervall die Einheiten an um Daten zu lesesn
            for i in range(len(HC05S)):
                hc05lib.send_to_device(HC05S[i], f"{CMD_WRITE[7]}=")

        # BT-Daten von den Einheiten lesen
        device_data = hc05lib.readdata(HC05S, CMD_READ, CMD_WRITE, device_data)

        # Zeit-Sync an die Einheiten senden
        hc05lib.time_sync(HC05S, CMD_WRITE)

# Ende der Hauptschleife
except KeyboardInterrupt:
    print("Beende auf Wunsch (Ctrl+C)...")

finally:
    try:
        # Alle Verbindungen sauber schließen
        hc05lib.stop_all()
        pasco2.write_value(
            pasco2.REG_MEAS_CFG,
            pasco2.read_value(pasco2.REG_MEAS_CFG) & 0b11111100,
        )  # set mode to idle
        pasco2.bus.close()
        bus.close()
    except Exception:
        pass
    print("Alles gestoppt.")