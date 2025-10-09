# hc05lib.py 
#
# Autor: Luca Knapp
# Datum: 09.10.2025
# Version: 2.1
# Beschreibung: Bibliothek zur Kommunikation mit HC-05 Modulen via Bluetooth
#

import bluetooth
import time
import os
import threading

# ---------------------------
# Dictonaries
# ---------------------------

connected_devices = {}   # mac -> socket
connecting = {}          # merkt, ob gerade verbunden wird
last_mac_list = []       # merkt sich zuletzt gestartete Liste (HC05S)


connector_thread = False # Variable für den Thread

# ---------------------------
# Parameter
# ---------------------------

RETRY_DELAY_S   = 2.0    # Wartezeit zwischen Verbindungs-Versuchen
READ_TIMEOUT_S  = 0.10   # kurzer Lese-Timeout pro recv()

# ---------------------------
# Connecticon-Management
# ---------------------------

def restart_bluetooth():
    # Bluetooth-Dienst neu starten
    # Nach 10 Retrys
    os.system("sudo systemctl restart bluetooth")
    os.system("rfkill unblock all")
    time.sleep(2)

def connect_once(mac):
    """Versucht einmal zu verbinden (blocking ist ok, läuft im Hintergrund-Thread)."""
    
    # Falls noch ein alter/beschädigter Socket existiert schließen
    old = connected_devices.pop(mac, None)
    if old:
        try:
            old.close()
        except Exception:
            pass

        # Neuen Socket erstellen und verbinden
    sock = None
    try:
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        # WICHTIG: KEIN settimeout() VOR connect() -> vermeidet Errno 77
        sock.connect((mac, 1))               # baut Verbindung auf Port 1 (SPP)
        sock.settimeout(READ_TIMEOUT_S)      # kurzer Timeout fürs spätere Lesen
        connected_devices[mac] = sock        # merkt Socket im Dict
        print(f"Verbunden mit {mac}")
        return True                          # Erfolg
    
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

def conn_loop():
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
            # Schon am Verbinden (Holt mit der Mak aus dem Dict True/False)
            if connecting.get(mac):
                continue

            # Neuen Verbindungsversuch starten
            connecting[mac] = True
            ok = connect_once(mac) # Versucht zu verbinden
            if not ok:             # Bei Fehlern zählen
                fail_count += 1
            else:                  # Bei Erfolg zurücksetzen
                fail_count = 0

        # Wenn lange gar nichts klappt, BT-Dienst einmal neu starten
        if fail_count >= 10:
            print("Viele Verbindungsfehler -> Bluetooth neu starten …")
            restart_bluetooth()
            fail_count = 0

        time.sleep(RETRY_DELAY_S)

# ---------------------------
# Geräte-Management
# ---------------------------

def stop_device(mac_address):
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

def start_all(mac_list):
    """Startet alle BT Geräte (HC05) und den Hintergrund-Thread."""
    global connector_thread
    
    # Löscht alte Verbindungen
    last_mac_list.clear()
    # Fügt neue hinzu
    last_mac_list.extend(mac_list)

    if not connector_thread:
        threading.Thread(target=conn_loop, daemon=True).start()
        connector_thread = True # Thread wurde gestartet

def stop_all():
    """Stoppt alle Geräte aus dem Dict."""
    for mac in list(connected_devices.keys()):
        stop_device(mac)

# ---------------------------
# Kommunikation
# ---------------------------

def send_to_device(mac_address, msg):
    """
    Sendet Nachricht an ein Gerät.
    Blockiert nicht beim Reconnect – das macht der Hintergrund-Thread.
    """
    sock = connected_devices.get(mac_address)       # Holt aus dem Dict info MAC und Socket Objekt
    if not sock:                                    # Wenn nicht verbunden.
        print(f"{mac_address} ist nicht verbunden (Senden übersprungen).")
        return
    if not msg.endswith("\n"):                      # Checkt ob Zeilenumbruch gesetzt wurde
        msg += "\n"
    try:
        sock.send(msg)                              # Sendet Nachricht
        # print(f"Gesendet an {mac_address}: {msg.strip()}")
    except bluetooth.btcommon.BluetoothError as e:
        print(f"Sende-Fehler an {mac_address}: {e}")
        # Verbindung als „tot“ markieren; Daemon verbindet neu
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

def read_from_device(mac_address, timeout: float = READ_TIMEOUT_S) -> str | None:
    """
    Liest eine Zeile vom Gerät mit kurzem Timeout.
    Reconnects passieren im Hintergrund; hier nur kurzer Versuch.
    """
    sock = connected_devices.get(mac_address)       # Holt aus dem Dict info MAC und Socket Objekt
    
    if not sock:                                    # Wenn nicht verbunden
        return None

    try:
        # timeout 0.0 verursacht Disconnects -> lieber minimalen Wert nehmen
        if timeout is None or timeout <= 0.0:
            timeout = 0.05
        sock.settimeout(timeout)

        data = b""                                  # byteString Rohe Bytes
        while True:
            chunk = sock.recv(1)                    # liest Byte für Byte
            if not chunk:
                # Gegenstelle hat sauber geschlossen -> als echter Fehler behandeln
                raise bluetooth.btcommon.BluetoothError("peer closed")
            if chunk == b"\n":                      # Ende der Zeile
                return data.decode("utf-8", errors="ignore").strip()
            data += chunk

    except bluetooth.btcommon.BluetoothError as e:
        s = str(e).lower()

        # Wenn einfach nichts kam -> KEIN harter Fehler, nur None zurückgeben
        if "timed out" in s or "timeout" in s or "would block" in s:
            return None
        
        # andere Fehler -> Verbindung wirklich gestört -> reconnecten lassen
        try:
            sock.close()
        except Exception:
            pass
        connected_devices.pop(mac_address, None)
        connecting[mac_address] = False
        return None

    except Exception as e:
        # Unbekannter Fehler -> Verbindung als tot markieren
        # (z. B. OSError von darunterliegenden Schichten)
        try:
            sock.close()
        except Exception:
            pass
        connected_devices.pop(mac_address, None) # Entfernt aus Dict
        connecting[mac_address] = False          # Entfernt aus Dict bzw schreibt false
        return None

def readdata(HC05S, cmd_read, cmd_write, device_data):
    """
    Erste Schleife geht Liste durch zwichen den Geräten in HC05S 
    Liest, Checkt ob info zur Einheit kommt und Speichert
    Geht kurz Nachrichten durch, die anliegen (kleines Sammelfenster)
    """
    for z in range(len(HC05S)):
        # 1) Erste Zeile (typisch "unit=") mit normalem kurzem Timeout
        msg = read_from_device(HC05S[z], timeout=0.10)
        if msg and msg.startswith("unit="):
            parts = msg.split("=", 1)
            if len(parts) == 2:
                device_data[z][0] = parts[1]

            # 2) Jetzt noch sehr kurz weitere Zeilen einsammeln
            t_end = time.time() + 0.08  # ~80 ms Sammelzeit
            while time.time() < t_end:
                m = read_from_device(HC05S[z], timeout=0.05)
                if not m:
                    # in diesem Mini-Fenster kam gerade nichts -> weiter sammeln
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

def writedata(HC05S, cmd_write, co2):
    """
    Enscheidet wie hoch die Lüfterstufe ist und
    Schreibt die Lüfterstufe an alle Geräte
    """
    for p in range(len(HC05S)):
        if co2 == 0:
            # Sensorfehler ? Fallback
            fan_percent = 30

        elif co2 < 700:
            fan_percent = 30  # Minimalbetrieb

        elif 700 <= co2 < 1200:
            # Lüfterleistung steigt linear zwischen 25..85 %
            fan_percent = 25 + (co2 - 700) * (60 / 500)

        elif co2 >= 1200:
            fan_percent = 90   # Vollgas
        
        # Lüfterstufe an die Einheit senden
        send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")

def write_off(HC05S, cmd_write):
    """
    Schreibt die Lüfterstufe 0 an alle Geräte
    """
    for p in range(len(HC05S)):
        fan_percent = 0
        send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")

# globale Variable für Zeit-Sync
delay_time_send = 0
def time_sync(HC05S, cmd_write):
    """
    Sendet die aktuelle Zeit an alle Geräte
    """
    global delay_time_send
    jetzt = time.time()
    uhrzeit = time.ctime(time.time())

    if jetzt >= delay_time_send:  # Tag=Mon, Monat=Jan, Tag=01, Zeit=12:00:00, Jahr=2025 an die Einheiten gesendet
        parts = uhrzeit.split()
        for p in range(len(HC05S)):
            for i in range(len(parts)):
                send_to_device(HC05S[p], f"{cmd_write[i]}={parts[i]}")
                time.sleep(0.1)
                # print(f"Gesendet an Einheit {p+1}: {cmd_write[i]}={parts[i]}")
        print(f"Zeit-Sync gesendet: {uhrzeit}\n")
        delay_time_send = jetzt + 3600  # alle 60 Minuten
