# weblib.py
# Luca Knapp

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
    for i, dev in enumerate(device_data, start=1):
        payload.update({
            f"device{i}": dev[0],
            f"tempinnen{i}": dev[7],
            f"huminnen{i}": dev[6],
            f"tempaussen{i}": dev[5],
            f"humaussen{i}": dev[8],
            f"drehzahl{i}": dev[2],
            f"periode{i}": dev[4],
        })

    return payload

def write_json(d, TMP, OUT):
    TMP.write_text(json.dumps(d, ensure_ascii=False))
    os.replace(TMP, OUT)