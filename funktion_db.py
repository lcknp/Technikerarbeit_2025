#   funktion_db.py
#   by Luca Knapp
#
#   Database Funktion
#   v0.2
#
#   11.09.2025
#
#  Copyright 2025

import pymysql
import time

def databasesafe(device, uhrzeit, co2=None, temp=None, humi=None, pressure=None, temp_in=None, humi_in=None, temp_out=None, humi_out=None):
    """
    Speichert Messwerte in einer Monats-Tabelle (Messungen_YYYYMM).
    - uhrzeit: String im Format "%a %b %d %H:%M:%S %Y"
    - device: Ger�tename (z.B. 'raspi1', 'ardu1', ...)
    - Messwerte: als float oder None
    """

    # String -> struct_time parsen
    t = time.strptime(uhrzeit, "%a %b %d %H:%M:%S %Y")
    # struct_time -> ISO-Format für DB
    #iso_str = time.strftime("%Y-%m-%d %H:%M:%S", t)
    # Tabellennamen: YYYYMM
    #ym = time.strftime("%Y%m", t)

    #Verbindung zur DB öffnen
    db = pymysql.connect(
        host="localhost",
        user="luca",
        password="12345678",
        database="data",
        autocommit=True
    )
    
    cur = db.cursor()
    
    table_name = f"Messungen_{t.tm_year}{t.tm_mon:02d}"
    
    #Tabelle erstellen, falls nicht vorhanden
    create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            uhrzeit VARCHAR(50),
            device VARCHAR(50),
            co2 DOUBLE NULL,
            temp DOUBLE NULL,
            humi DOUBLE NULL,
            pressure DOUBLE NULL,
            temp_in DOUBLE NULL,
            humi_in DOUBLE NULL,
            temp_out DOUBLE NULL,
            humi_out DOUBLE NULL
        )
    """
    cur.execute(create_sql)

    #Datensatz speichern
    insert_sql = f"""
        INSERT INTO {table_name}
        (uhrzeit, device, co2, temp, humi, pressure, temp_in, humi_in, temp_out, humi_out)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            co2=VALUES(co2),
            temp=VALUES(temp),
            humi=VALUES(humi),
            pressure=VALUES(pressure),
            temp_in=VALUES(temp_in),
            humi_in=VALUES(humi_in),
            temp_out=VALUES(temp_out),
            humi_out=VALUES(humi_out);
    """
    cur.execute(insert_sql, (uhrzeit, device, co2, temp, humi, pressure, temp_in, humi_in, temp_out, humi_out))
    print(f"Daten gespeichert in {table_name}!\n")

    # Verbindung schließen
    cur.close()
    db.close()
