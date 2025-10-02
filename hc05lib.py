# hc05lib.py — einfache Version mit Hintergrund-Thread und deinen Kommentaren

import bluetooth
import time
import os
import threading

#Dictionary, um aktive Verbindungen zu speichern
connected_devices = {}   # mac -> socket
connecting = {}          # merkt, ob gerade verbunden wird
last_mac_list = []       # merkt sich zuletzt gestartete Liste (HC05S)
_daemon_started = False  # startet den Loop nur einmal

# ---------------------------
# Parameter
# ---------------------------
RETRY_DELAY_S   = 2.0    # Wartezeit zwischen Verbindungs-Versuchen
READ_TIMEOUT_S  = 0.2    # kurzer Lese-Timeout pro recv()

# ---------------------------
# Helfer
# ---------------------------

def restart_bluetooth():
    #Bluetooth-Dienst neu starten (falls lange keine Verbindung zustande kommt)
    os.system("sudo systemctl restart bluetooth")
    os.system("rfkill unblock all")
    time.sleep(2)

def _connect_once(mac):
    """Versucht einmal zu verbinden (blocking ist ok, läuft im Hintergrund-Thread)."""
    # Falls noch ein alter/beschädigter Socket existiert: schließen
    old = connected_devices.pop(mac, None)
    if old:
        try:
            old.close()
        except Exception:
            pass

    try:
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        #WICHTIG: KEIN settimeout() VOR connect() -> vermeidet Errno 77
        sock.connect((mac, 1))                       #baut verbindung auf Port 1 Serial Port Profile
        sock.settimeout(READ_TIMEOUT_S)              #kurzer Timeout fürs spätere Lesen
        connected_devices[mac] = sock                #merkt Socket im Dict
        print(f"Verbunden mit {mac}")
        return True
    except Exception as e:
        print(f"Fehler beim Verbinden mit {mac}: {e}")
        try:
            sock.close()
        except Exception:
            pass
        return False
    finally:
        #„Verbinde gerade…“ zurücksetzen – der Daemon entscheidet über den nächsten Versuch
        connecting[mac] = False

def _conn_daemon():
    """Läuft im Hintergrund, hält alle Geräte verbunden (Reconnect im Loop)."""
    fail_count = 0
    while True:
        if not last_mac_list:
            time.sleep(1.0)
            continue

        for mac in list(last_mac_list):
            #Schon verbunden?
            if mac in connected_devices:
                continue
            #Schon am Verbinden?
            if connecting.get(mac):
                continue

            #Neuen Verbindungsversuch starten
            connecting[mac] = True
            ok = _connect_once(mac)
            if not ok:
                fail_count += 1
            else:
                fail_count = 0

        #Wenn lange gar nichts klappt, BT-Dienst einmal neu starten
        if fail_count >= 10:
            print("Viele Verbindungsfehler -> Bluetooth neu starten …")
            restart_bluetooth()
            fail_count = 0

        time.sleep(RETRY_DELAY_S)

# ---------------------------
# Geräte-Management
# ---------------------------

def start_device(mac_address):
    """Nicht-blockierend: Gerät zur Beobachtung hinzufügen."""
    if mac_address not in last_mac_list:
        last_mac_list.append(mac_address)

def stop_device(mac_address):
    """Sofort trennen (nicht-blockierend)."""
    sock = connected_devices.pop(mac_address, None)
    if sock:
        try:
            sock.close() #Schliest die Verbidnung
        except Exception:
            pass
    #Löscht aus der Beobachtungsliste
    try:
        last_mac_list.remove(mac_address)
    except ValueError:
        pass
    connecting[mac_address] = False
    print(f"Verbindung zu {mac_address} getrennt.")

def start_all(mac_list):
    """Startet alle BT Geräte (HC05) und den Hintergrund-Thread."""
    global _daemon_started
    last_mac_list.clear()
    last_mac_list.extend(mac_list)
    if not _daemon_started:
        threading.Thread(target=_conn_daemon, daemon=True).start()
        _daemon_started = True

def stop_all():
    """Stopt alle Geräte aus dem Dict"""
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
    sock = connected_devices.get(mac_address)       #Holt aus dem Dict info MAC und Socket Objekt
    if not sock:                                    #Wenn nicht verbunden.
        print(f"{mac_address} ist nicht verbunden (Senden übersprungen).")
        return
    if not msg.endswith("\n"):                      #Checkt ob Zeilenumbruch gesetzt wurde
        msg += "\n"
    try:
        sock.send(msg)                              #Sendet Nachricht
        #print(f"Gesendet an {mac_address}: {msg.strip()}")
    except Exception as e:
        print(f"Sende-Fehler an {mac_address}: {e}")
        #Verbindung als „tot“ markieren; Daemon verbindet neu
        try:
            sock.close()
        except Exception:
            pass
        connected_devices.pop(mac_address, None)
        connecting[mac_address] = False

def read_from_device(mac_address: str, timeout: float = READ_TIMEOUT_S) -> str | None:
    """
    Liest eine Zeile vom Gerät mit kurzem Timeout.
    Reconnects passieren im Hintergrund; hier nur kurzer Versuch.
    """
    sock = connected_devices.get(mac_address)       #Holt aus dem Dict info MAC und Socket Objekt
    if not sock:                                    #Wenn nicht verbunden
        return None

    #Setzt kurzfristig den gewünschten Timeout fürs Lesen
    try:
        sock.settimeout(timeout)                    #Setzt Timeout
        data = b""                                  #byteString Rohe Bytes
        while True:
            chunk = sock.recv(1)                    #liest Byte für Byte
            if not chunk:
                return None                         #Wenn nichts gekommen ist
            if chunk == b"\n":                      #Ende der Zeile/Wenn in chunk ein /n Byte ist
                return data.decode("utf-8", errors="ignore").strip()
            data += chunk                           #fügt Stück für Stück in der While Schleife zu data die einzelnen Buchstaben hinzu
    except Exception:
        #Falls ein Fehler passiert ist: Verbindung schließen; Daemon reconnectet
        try:
            sock.close()
        except Exception:
            pass
        connected_devices.pop(mac_address, None)
        connecting[mac_address] = False
        return None

def readdata(HC05S, cmd_read, cmd_write, device_data):
    """
    Erste Schleife geht Liste durch zwichen den Geräten in HC05S 
    Liest, Checkt ob info zur Einheit kommt und Speichert
    Geht so viele Nachtichten durch wie in der cmd_read liste stehen 
    """

    for z in range(len(HC05S)):
        msg = read_from_device(HC05S[z])
        if msg:
            if msg.startswith("unit="):
                parts = msg.split("=")
                device_data[z][0] = parts[1]
                
                for x in range(len(cmd_read)+1):
                    msg = read_from_device(HC05S[z], timeout=0.0)
                    if msg:
                        for y in range(len(cmd_read)):
                            if msg.startswith(cmd_read[y]):
                                parts = msg.split("=")
                                device_data[z][y] = parts[1].replace("°C", "").replace("%", "").replace("U/min", "")                                
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
                send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")
                mode = "FALLBACK"

            elif co2 < 700:
                fan_percent = 30
                send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")
                mode = "IDLE"

            elif 700 <= co2 < 1200:
                # Lüfterleistung steigt linear zwischen 20?80 %
                fan_percent = 25 + (co2 - 700) * (60 / 500)
                send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")
                mode = "NORMAL"

            elif co2 >= 1200:
                fan_percent = 90   # Vollgas
                send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")
                mode = "BOOST"
                
            send_to_device(HC05S[p], f"{cmd_write[6]}=90000")

def write_off(HC05S, cmd_write):
    """
    Schreibt die Lüfterstufe 0 an alle Geräte
    """
    for p in range(len(HC05S)):
            fan_percent = 0
            send_to_device(HC05S[p], f"{cmd_write[5]}={fan_percent}")
            mode = "OFF"

delay_time_send = 0  # globale Variable für Zeit-Sync
def time_sync(HC05S, cmd_write):
    """
    Sendet die aktuelle Zeit an alle Geräte
    """
    global delay_time_send
    jetzt = time.time()
    uhrzeit = time.ctime(time.time())

    if jetzt >= delay_time_send: #Tag=Mon, Monat=Jan, Tag=01, Zeit=12:00:00, Jahr=2025 an die Einheiten gesendet
            parts = uhrzeit.split()
            for p in range(len(HC05S)):
                for i in range(len(parts)):
                    send_to_device(HC05S[p], f"{cmd_write[i]}={parts[i]}")
                    time.sleep(0.1)
                    #print(f"Gesendet an Einheit {p+1}: {cmd_write[i]}={parts[i]}")
            print(f"Zeit-Sync gesendet: {uhrzeit}\n")
            delay_time_send = jetzt +  3600  # alle 60 Minuten