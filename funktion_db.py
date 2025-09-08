#   funktion_db.py
#   by Luca Knapp
#
#   Database Funktion
#   v0.1
#
#   26.08.2025
#
#  Copyright 2025

import pymysql
import time

# Globale Einstellung: soll die DB beim Start geleert werden?
reset_db = False   # ? True = Tabelle wird auf 0 gesetzt

def databasesafe(device, uhrzeit, co2, temp, humi, pressure):
    
    # String -> struct_time parsen
    t = time.strptime(uhrzeit, "%a %b %d %H:%M:%S %Y")
    # struct_time -> ISO-Format für DB
    #iso_str = time.strftime("%Y-%m-%d %H:%M:%S", t)
    # Tabellennamen: YYYYMM
    #ym = time.strftime("%Y%m", t)

    # Verbindung zur DB öffnen
    db = pymysql.connect(
        host="localhost",
        user="luca",
        password="12345678",
        database="data",
        autocommit=True
    )
    
    cur = db.cursor()
    
    table_name = f"Messungen_{t.tm_year}{t.tm_mon:02d}"
    
    create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            uhrzeit VARCHAR(50),
            device VARCHAR(50),
            co2 DECIMAL(10,2),
            temp DECIMAL(6,2),
            humi DECIMAL(6,2),
            pressure DECIMAL(8,2)
        )
    """
    cur.execute(create_sql)

    # Wenn reset_db aktiv: Tabelle leeren
    if reset_db:
        cur.execute(f"TRUNCATE TABLE {table_name}")
        print(f"Tabelle {table_name} wurde zurückgesetzt!")

    # Datensatz speichern
    insert_sql = f"""
        INSERT INTO {table_name} (uhrzeit, device, co2, temp, humi, pressure)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cur.execute(insert_sql, (uhrzeit, device, co2, temp, humi, pressure))
    print(f"Daten gespeichert in {table_name}!\n")

    # Verbindung schließen
    cur.close()
    db.close()
