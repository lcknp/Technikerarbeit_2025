import bluetooth
import time

#Dictionary, um aktive Verbindungen zu speichern
connected_devices = {}

#"98:D3:31:FC:12:34": <bluetooth.BluetoothSocket object at 0x...>,
#"00:14:03:06:66:2A": <bluetooth.BluetoothSocket object at 0x...>

# ---------------------------
# Geräte-Management
# ---------------------------

def start_device(mac_address):
    if mac_address in connected_devices:
        print(f"Gerät {mac_address} ist schon verbunden.")
        return

    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    #Baut eine Virtuelle Schnittstelle auf
    try:
        sock.connect((mac_address, 1))
        #baut verbindung auf Port 1 Serial Port Profile
        connected_devices[mac_address] = sock
        print(f"Verbunden mit {mac_address}")
    except Exception as e:
        print(f"Fehler beim Verbinden mit {mac_address}: {e}")

def stop_device(mac_address):
    sock = connected_devices.get(mac_address)
    if sock:
        sock.close() #Schliest die Verbidnung 
        del connected_devices[mac_address] #Löscht aus dem Dict
        print(f"Verbindung zu {mac_address} getrennt.")

#Startet alle BT Geräte (HC05) Liste weitergeben
def start_all(mac_list):
    for mac in mac_list:
        start_device(mac)
        time.sleep(2)

#Stopt alle geräte aus dem Dict
def stop_all():
    for mac in list(connected_devices.keys()):
        stop_device(mac)

# ---------------------------
# Kommunikation
# ---------------------------
def send_to_device(mac_address, msg):
    sock = connected_devices.get(mac_address)       #Holt aus dem Dict info MAC und Socket Objekt
    if not sock:                                    #Wenn nicht verbunden.
        print(f"{mac_address} ist nicht verbunden.")
        return
    if not msg.endswith("\n"):                      #Checkt ob Zeilenumbruch gesetzt wurde
        msg += "\n"
    try:
        sock.send(msg)                              #Sendet Nachricht
        #print(f"Gesendet an {mac_address}: {msg.strip()}")
    except Exception as e:
        print(f"Fehler beim Senden an {mac_address}: {e}")
        stop_device(mac_address)
        start_device(mac_address)

def read_from_device(mac_address: str, timeout: float = 1.0) -> str | None:
    sock = connected_devices.get(mac_address)       #Holt aus dem Dict info MAC und Socket Objekt
    if not sock:                                    #Wenn nicht verbunden
        print(f"{mac_address} ist nicht verbunden.")
        stop_device(mac_address)
        start_device(mac_address)
        return None

    sock.settimeout(timeout)                        #Setzt Timeout
    data = b""                                      #byteString Rohe Bytes
    try:
        while True:
            chunk = sock.recv(1)                    #liest Byte für Byte
            if not chunk:
                return None                         #Wenn nichts gekommen ist
            if chunk == b"\n":                      #Ende der Zeile/Wenn in chunk ein /n Byte ist
                return data.decode("utf-8", errors="ignore").strip()
            data += chunk                           #fügt Stück für Stück in der While Schleife zu data die einzelnen Buchstaben hinzu
    except bluetooth.btcommon.BluetoothError:       #Falls ein fehler Passiert geht er raus
        return None

def readdata(HC05S, cmd_read, device_data):
    
    #global device_data
    
    #Erste Schleife geht Liste durch zwichen den Geräten in HC05S 
    #Liest, Checkt ob info zur Einheit kommt und Speichert
    #Geht so viele Nachtichten durch wie in der cmd_read liste stehen 
    
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
