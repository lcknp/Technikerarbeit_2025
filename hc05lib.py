# =============================================================================
#  Projekt:      EBM-Papst Lüftungssteuerung – Technikerarbeit 2025/26
#  Datei:        hc05lib.py
#  Autor:        Luca Knapp
#  Version:      2.1
#  Datum:        2025
#
#  Beschreibung: Bibliothek zur Kommunikation mit HC-05 Modulen via Bluetooth
#  
#  Lizenz:
#   Dieses Projekt wurde im Rahmen der Technikerarbeit 2025/26 erstellt.
#   Nutzung und Weitergabe nur mit Erlaubnis des Autors.
#
# =============================================================================

from __future__ import annotations

import os
import threading
import time

import bluetooth

# ---------------------------
# Dictonaries
# ---------------------------

connected_devices: dict[str, bluetooth.BluetoothSocket] = {}  # mac -> socket
connecting: dict[str, bool] = {}  # merkt, ob gerade verbunden wird
last_mac_list: list[str] = []  # merkt sich zuletzt gestartete Liste (HC05S)

_connector_thread_started = False  # Variable für den Thread

# ---------------------------
# Parameter
# ---------------------------

RETRY_DELAY_S = 2.0  # Wartezeit zwischen Verbindungs-Versuchen
READ_TIMEOUT_S = 0.10  # kurzer Lese-Timeout pro recv()

# ---- Globale Variablen ----
push_pull_delay = 0.0
direction = 0
master_cmd = "0"  # 0=aufladen, 1=entladen (Startzustand)
prev_master_cmd: str | None = None
delayed_until: list[float] = []  # pro Einheit Nachlauf-Endzeit (Sekunden-Timestamp)

# globale Variable für Zeit-Sync
delay_time_send = 0.0


# ---------------------------
# Connecticon-Management
# ---------------------------


def _restart_bluetooth() -> None:
    # Bluetooth-Dienst neu starten
    # Nach 10 Retrys
    os.system("sudo systemctl restart bluetooth")
    os.system("rfkill unblock all")
    time.sleep(2)


def _connect_once(mac: str) -> bool:
    """Versucht einmal zu verbinden (blocking ist ok, läuft im Hintergrund-Thread)."""

    # Falls noch ein alter/beschädigter Socket existiert schließen
    old = connected_devices.pop(mac, None)
    if old:
        try:
            old.close()
        except Exception:
            pass

    # Neuen Socket erstellen und verbinden
    sock: bluetooth.BluetoothSocket | None = None
    try:
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((mac, 1))  # baut Verbindung auf Port 1 (SPP)
        sock.settimeout(READ_TIMEOUT_S)  # kurzer Timeout fürs spätere Lesen
        connected_devices[mac] = sock  # merkt Socket im Dict
        print(f"Verbunden mit {mac}")
        return True  # Erfolg

    # Bei Fehlern Socket schließen und aufräumen
    except Exception as e:
        print(f"Fehler beim Verbinden mit {mac}: {e}")
        try:
            if sock:
                sock.close()
        except Exception:
            pass
        return False

    finally:
        # „Verbinde gerade…“ zurücksetzen – der Daemon entscheidet über den nächsten Versuch
        connecting[mac] = False


def _conn_loop() -> None:
    """Läuft im Hintergrund, hält alle Geräte verbunden
    (Reconnect im Loop)."""

    fail_count = 0

    # Connect - loop
    while True:
        # Keine Geräte in der Liste kurz warten
        if not last_mac_list:
            time.sleep(1.0)
            continue

        # Geht die Liste durch und versucht zu verbinden
        for mac in list(last_mac_list):
            # Schon verbunden?
            if mac in connected_devices:
                continue
            # Schon am Verbinden (Holt mit der Mac aus dem Dict True/False)
            if connecting.get(mac):
                continue

            # Neuen Verbindungsversuch starten
            connecting[mac] = True
            ok = _connect_once(mac)  # Versucht zu verbinden
            if not ok:  # Bei Fehlern zählen
                fail_count += 1
            else:  # Bei Erfolg zurücksetzen
                fail_count = 0

        # Wenn lange gar nichts klappt, BT-Dienst einmal neu starten
        if fail_count >= 10:
            print("Viele Verbindungsfehler -> Bluetooth neu starten …")
            _restart_bluetooth()
            fail_count = 0

        time.sleep(RETRY_DELAY_S)


# ---------------------------
# Geräte-Management
# ---------------------------


def stop_device(mac_address: str) -> None:
    """Sofort trennen (nicht-blockierend)."""
    sock = connected_devices.pop(mac_address, None)
    if sock:
        try:
            sock.close()  # Schließt die Verbindung
        except Exception:
            pass
    # Löscht aus der Beobachtungsliste
    try:
        last_mac_list.remove(mac_address)
    except ValueError:
        pass
    connecting[mac_address] = False
    print(f"Verbindung zu {mac_address} getrennt.")


def start_all(mac_list: list[str]) -> None:
    """Startet alle BT Geräte (HC05) und den Hintergrund-Thread."""
    global _connector_thread_started

    # Löscht alte Verbindungen
    last_mac_list.clear()
    # Fügt neue hinzu
    last_mac_list.extend(mac_list)

    if not _connector_thread_started:
        threading.Thread(target=_conn_loop, daemon=True).start()
        _connector_thread_started = True  # Thread wurde gestartet


def stop_all() -> None:
    """Stoppt alle Geräte aus dem Dict."""
    for mac in list(connected_devices.keys()):
        stop_device(mac)


# ---------------------------
# Kommunikation
# ---------------------------


def send_to_device(mac_address: str, msg: str) -> None:
    """
    Sendet Nachricht an ein Gerät.
    Blockiert nicht beim Reconnect – das macht der Hintergrund-Thread.
    """
    sock = connected_devices.get(
        mac_address
    )  # Holt aus dem Dict info MAC und Socket Objekt
    if not sock:  # Wenn nicht verbunden.
        print(f"{mac_address} ist nicht verbunden (Senden übersprungen).")
        return
    if not msg.endswith("\n"):  # Checkt ob Zeilenumbruch gesetzt wurde
        msg += "\n"
    try:
        sock.send(msg)  # Sendet Nachricht
        # print(f"Gesendet an {mac_address}: {msg.strip()}")
    except bluetooth.btcommon.BluetoothError as e:
        print(f"Sende-Fehler an {mac_address}: {e}")
        # Verbindung als tot markieren; Daemon verbindet neu
        try:
            sock.close()
        except Exception:
            pass
        connected_devices.pop(mac_address, None)
        connecting[mac_address] = False
    except Exception as e:
        print(f"Unbekannter Sende-Fehler an {mac_address}: {e}")
        try:
            sock.close()
        except Exception:
            pass
        connected_devices.pop(mac_address, None)
        connecting[mac_address] = False


def _read_from_device(mac_address: str, timeout: float = READ_TIMEOUT_S) -> str | None:
    """
    Liest eine Zeile vom Gerät mit kurzem Timeout.
    Reconnects passieren im Hintergrund; hier nur kurzer Versuch.
    """
    sock = connected_devices.get(
        mac_address
    )  # Holt aus dem Dict info MAC und Socket Objekt

    if not sock:  # Wenn nicht verbunden
        return None

    try:
        # timeout 0.0 verursacht Disconnects
        if timeout <= 0.0:
            timeout = 0.05
        sock.settimeout(timeout)

        data = b""  # byteString Rohe Bytes
        while True:
            chunk = sock.recv(1)  # liest Byte für Byte
            if not chunk:
                # Gegenstelle hat sauber geschlossen
                raise bluetooth.btcommon.BluetoothError("peer closed")
            if chunk == b"\n":  # Ende der Zeile
                return data.decode("utf-8", errors="ignore").strip()
            data += chunk

    except bluetooth.btcommon.BluetoothError as e:
        s = str(e).lower()

        if "timed out" in s or "timeout" in s or "would block" in s:
            return None

        try:
            sock.close()
        except Exception:
            pass
        connected_devices.pop(mac_address, None)
        connecting[mac_address] = False
        return None

    except Exception:
        # Unbekannter Fehler -> Verbindung als tot markieren
        try:
            sock.close()
        except Exception:
            pass
        connected_devices.pop(mac_address, None)  # Entfernt aus Dict
        connecting[mac_address] = False  # Entfernt aus Dict bzw schreibt false
        return None


def readdata(hc05s: list[str], cmd_read: list[str], _cmd_write: list[str], device_data):
    """
    Erste Schleife geht Liste durch zwichen den Geräten in HC05S
    Liest, Checkt ob info zur Einheit kommt und Speichert
    Geht kurz Nachrichten durch, die anliegen (kleines Sammelfenster)
    """
    for z in range(len(hc05s)):
        # 1) Erste Zeile ("unit=") mit normalem kurzem Timeout
        msg = _read_from_device(hc05s[z], timeout=0.10)
        if msg and msg.startswith("unit="):
            parts = msg.split("=", 1)
            if len(parts) == 2:
                device_data[z][0] = parts[1]

            # 2) Jetzt noch sehr kurz weitere Zeilen einsammeln
            t_end = time.time() + 0.08  # ~80 ms Sammelzeit
            while time.time() < t_end:
                m = _read_from_device(hc05s[z], timeout=0.05)
                if not m:
                    # in diesem Mini-Fenster kam gerade nichts, weiter sammeln
                    continue
                for y, key in enumerate(cmd_read):
                    if m.startswith(key):
                        p = m.split("=", 1)
                        if len(p) == 2:
                            device_data[z][y] = (
                                p[1]
                                .replace("°C", "")
                                .replace("%", "")
                                .replace("U/min", "")
                            )
    return device_data


def writedata(hc05s: list[str], cmd_write: list[str], raspi_data, device_data) -> None:
    """
    Enscheidet wie hoch die Lüfterstufe ist und
    Schreibt die Lüfterstufe an alle Geräte
    Steuert auch die Laufrichtung
    """
    global push_pull_delay, direction, master_cmd, prev_master_cmd, delayed_until

    # sicherstellen, dass delayed_until zur Anzahl passt
    if len(delayed_until) != len(hc05s):
        delayed_until = [0.0] * len(hc05s)

    jetzt = time.time()

    # --- Lüfterleistung nach CO2  ---
    for p in range(len(hc05s)):
        if raspi_data[0] < 400:
            fan_percent = 1
        elif 400 <= raspi_data[0] < 1200:
            fan_percent = 35 + (raspi_data[0] - 400) * 0.06875
        else:
            fan_percent = 90
        send_to_device(hc05s[p], f"{cmd_write[5]}={fan_percent}")

    for i in range(len(hc05s)):
        # -----------------------
        # Push-Pull Steuerung ( < 20°C: Wärmerückgewinnung + Nachlauf )
        # -----------------------
        if float(device_data[0][5]) < 20:  # Außentemperatur kleiner als 20
            schaltschwelle = 20

            if i == 0:
                # --- MASTER ---
                t_m = float(device_data[0][7])

                # Master entscheidet
                if t_m > schaltschwelle:
                    master_cmd = "1"  # entladen
                elif t_m < 16:
                    master_cmd = "0"  # aufladen

                # an Master senden
                send_to_device(hc05s[0], f"{cmd_write[6]}={master_cmd}")

                # Richtungswechsel -> Nachlaufzeit für alle Slaves starten
                if (prev_master_cmd is None) or (master_cmd != prev_master_cmd):
                    for j in range(1, len(hc05s)):
                        delayed_until[j] = jetzt + 120
                    prev_master_cmd = master_cmd

            else:
                # --- SLAVES ---
                t_s = float(device_data[i][7])

                # Standard: Gegenphase zum Master
                slave_cmd = "0" if master_cmd == "1" else "1"

                # Nachlauf: weiter aufladen (0), solange Nachlaufzeit aktiv UND Schwelle nicht erreicht
                if (t_s < schaltschwelle) and (jetzt < delayed_until[i]):
                    slave_cmd = "0"
                else:
                    # Sobald Schwelle erreicht oder Nachlauf vorbei -> Nachlauf beenden
                    delayed_until[i] = 0.0

                # Befehl an Slave senden
                send_to_device(hc05s[i], f"{cmd_write[6]}={slave_cmd}")

        # -----------------------
        # Durchzug bei angenehmen Temperaturen
        # -----------------------
        if float(device_data[0][5]) > 20 and float(device_data[i][5]) < 27:
            direction = 0  # durchzug

        # -----------------------
        # zu hohen Aussentemperaturen – kurze Zykluszeiten
        # -----------------------
        if float(device_data[0][5]) > 27:
            if jetzt >= push_pull_delay:
                push_pull_delay = jetzt + 50  # + x Sekunden
                direction += 1  # 1=Push, 0=Pull
                if direction > 1:
                    direction = 0

        # -----------------------
        # Daten senden an Einheiten >20°C
        # -----------------------
        if float(device_data[0][5]) > 20:
            if direction == 0:
                dir_send = "1" if (i % 2 == 1) else "0"  # gerade=1, ungerade=0
            else:
                dir_send = "0" if (i % 2 == 1) else "1"  # gerade=0, ungerade=1
            send_to_device(hc05s[i], f"{cmd_write[6]}={dir_send}")


def write_off(hc05s: list[str], cmd_write: list[str]) -> None:
    """
    Schreibt die Lüfterstufe 0 an alle Geräte
    """
    for p in range(len(hc05s)):
        fan_percent = 1
        send_to_device(hc05s[p], f"{cmd_write[5]}={fan_percent}")


def time_sync(hc05s: list[str], cmd_write: list[str]) -> None:
    """
    Sendet die aktuelle Zeit an alle Geräte
    """
    global delay_time_send
    jetzt = time.time()
    uhrzeit = time.ctime(time.time())

    if jetzt >= delay_time_send:
        parts = uhrzeit.split()
        for p in range(len(hc05s)):
            for i in range(len(parts)):
                send_to_device(hc05s[p], f"{cmd_write[i]}={parts[i]}")
                time.sleep(0.1)
                # print(f"Gesendet an Einheit {p+1}: {cmd_write[i]}={parts[i]}")
        print(f"Zeit-Sync gesendet: {uhrzeit}\n")
        delay_time_send = jetzt + 3600  # alle 60 Minuten