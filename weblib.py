# =============================================================================
#  Projekt:      EBM-Papst Lüftungssteuerung – Technikerarbeit 2025/26
#  Datei:        weblib.py
#  Autor:        Luca Knapp
#  Version:      1.0
#  Datum:        2025
#
#  Beschreibung:
#  ---------------------------------------------------------------------------
#  Hilfsfunktionen zum Erstellen der JSON-Datenstruktur für die Weboberfläche
#  sowie zum atomaren Schreiben der JSON-Datei.
#
#  Lizenz:
#   Dieses Projekt wurde im Rahmen der Technikerarbeit 2025/26 erstellt.
#   Nutzung und Weitergabe nur mit Erlaubnis des Autors.
#
# =============================================================================

import json
import os


def build_web_payload(uhrzeit, raspi_data, device_data):
    payload = {
        "ts": uhrzeit,
        "co2": raspi_data[0],
        "t": raspi_data[1],
        "h": raspi_data[2],
        "p": raspi_data[3],
    }

    # Für jedes Gerät in der Liste device_data hinzufügen
    # emumerate ab 1, da device1, device2, ...
    for i, dev in enumerate(device_data, start=1):
        payload.update(
            {
                f"device{i}": dev[0],
                f"tempinnen{i}": dev[7],
                f"huminnen{i}": dev[6],
                f"tempaussen{i}": dev[5],
                f"humaussen{i}": dev[8],
                f"drehzahl{i}": dev[2],
                f"periode{i}": dev[4],
            }
        )

    return payload

# Atomar JSON-Datei schreiben
def write_json(data, tmp, out):
    tmp.write_text(json.dumps(data, ensure_ascii=False))
    os.replace(tmp, out)