# =============================================================================
#  Projekt:      EBM-Papst Lüftungssteuerung – Technikerarbeit 2025/26
#  Datei:        raspisenslib.py
#  Autor:        Luca Knapp
#  Version:      1.0
#  Datum:        2025
#
#  Beschreibung:
#  ---------------------------------------------------------------------------
#  Funktionen zum Auslesen der Raspberry Pi Sensorwerte (BME280 + PASCO2).
#  Speichert bei I2C-Fehlern die letzten gültigen Werte und gibt diese zurück.
#
#  Lizenz:
#   Dieses Projekt wurde im Rahmen der Technikerarbeit 2025/26 erstellt.
#   Nutzung und Weitergabe nur mit Erlaubnis des Autors.
#
# =============================================================================

import pasco2

old_raspi_data = [0, 0, 0, 0, 0]


def raspi_readdata(bme280):
    global old_raspi_data

    # Starte mit den alten Werten
    raspi_data = old_raspi_data.copy()

    raspi_data[0] = pasco2.read_co2()

    try:
        raspi_data[1] = bme280.temperature
        raspi_data[1] = raspi_data[1] - 10  # Korrekturwert für die Temperatur
        raspi_data[2] = bme280.humidity
        raspi_data[3] = bme280.pressure
        raspi_data[4] = bme280.altitude
    except OSError:
        print("BME280 Fehler")

    old_raspi_data = raspi_data.copy()
    return raspi_data